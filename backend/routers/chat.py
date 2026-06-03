import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from agent.base import (
    WRITE_TOOL_NAMES,
    WRITE_TOOL_RESOURCES,
    _THINK_CLOSE,
    _THINK_OPEN,
    _detect_intent,
    _partial_tag,
    _to_lc_messages,
    get_student_context,
    make_tools,
)
from agent.llm_pool import ROLE_CHAT, ROLE_CLASSIFY, get_pool

_INTENT_SYSTEM = (
    'Classify the student message. Reply ONLY with valid JSON: {"intent": "<value>"}\n'
    "Values (pick exactly one):\n"
    "  tutoring      — academic subject question (explain, define, how does X work, give example)\n"
    "  performance   — asking about their own results, scores, progress, or how they are doing\n"
    "  recommendation — asking what course, topic, or module to study next\n"
    "  wellbeing     — expressing stress, overwhelm, exhaustion, or difficulty coping\n"
    "  general       — anything else (assignments, schedule, reminders, study plan, chitchat)\n"
    "No explanation. JSON only."
)


async def _classify_intent(text: str) -> str:
    """Non-streaming LLM call on a `classify` endpoint → structured JSON intent."""
    if not text.strip():
        return "general"
    try:
        async with get_pool().acquire(ROLE_CLASSIFY) as lease:
            classifier = lease.chat(temperature=0.0, max_tokens=20)
            result = await classifier.ainvoke([
                SystemMessage(content=_INTENT_SYSTEM),
                HumanMessage(content=text),
            ])
        data = json.loads(result.content.strip())
        intent = data.get("intent", "general")
        return intent if intent in ("tutoring", "performance", "recommendation", "wellbeing", "general") else "general"
    except Exception:
        return _detect_intent(text)  # keyword fallback on any failure

router = APIRouter()

# recursion_limit ≈ max_iterations × 3  (LLM call + tool + housekeeping per iter)
_PROACTIVE_LIMIT = 9   # ~3 iterations
_QA_LIMIT = 15         # ~5 iterations


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatRequest(BaseModel):
    student_id: int
    messages: list[ChatMessage]


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(req: ChatRequest):
    msgs = req.messages
    if msgs and msgs[-1].role == "user":
        user_input = msgs[-1].content or ""
        history_lc = _to_lc_messages(msgs[:-1])
    else:
        user_input = ""
        history_lc = _to_lc_messages(msgs)

    ctx = await get_student_context(req.student_id)
    context_block = (
        f"Student: {ctx['full_name']} (ID: {req.student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f} | Flags: {ctx['risk_flags']}\n"
        f"Unsubmitted: {ctx['unsubmitted_count']} | Next due: day {ctx['next_due']}\n"
    )

    gaps = ctx.get("prerequisite_gaps", [])
    gaps_note = f"Prerequisite gaps: {', '.join(gaps)}." if gaps else ""

    tools = make_tools(req.student_id)

    proactive_system = (
        "You are a proactive student advisor running a background check.\n"
        + context_block
        + "Check get_assignments and get_schedule for urgent items.\n"
        "If a deadline is within 3 days, risk_score > 0.7, or study sessions are missing: "
        "take ONE targeted write action (create_reminder or update_study_plan).\n"
        "Do NOT repeat tool calls. Stop as soon as you have acted or confirmed no action needed."
    )

    intent = await _classify_intent(user_input)

    if intent == "tutoring":
        qa_system = (
            "You are an expert academic tutor.\n"
            + context_block
            + gaps_note + "\n"
            + "Teaching approach:\n"
            "- Use clear explanations with concrete examples from the student's module\n"
            "- If the topic relates to a prerequisite gap, acknowledge it and bridge the gap\n"
            "- Use step-by-step breakdowns for complex concepts\n"
            "- End with a quick check: one question to confirm understanding\n"
            "After your explanation: call update_knowledge_state for the concept you just taught.\n"
            "  Use evidence_type='tutor_interaction' and score: 0.5 (brief), 0.7 (detailed), 0.9 (full worked example).\n"
            "Answer in the same language as the student (Vietnamese or English)."
        )
    elif intent == "performance":
        qa_system = (
            "You are a performance analysis assistant.\n"
            + context_block
            + "The student wants to understand how they are performing.\n"
            "Steps:\n"
            "1. Call get_student_profile to get VLE engagement and risk data.\n"
            "2. Call get_knowledge_state to see concept mastery.\n"
            "3. Call get_assignments to see scores and upcoming deadlines.\n"
            "4. Summarise clearly: strengths, weak concepts, VLE trend, next priority action.\n"
            "Be specific — name the concepts, modules, and scores. Answer in the same language as the student."
        )
    elif intent == "recommendation":
        qa_system = (
            "You are a course recommendation advisor.\n"
            + context_block
            + "The student wants to know what to study next.\n"
            "Steps:\n"
            "1. Call get_course_recommendations to get courses ready vs not ready based on mastery.\n"
            "2. Call get_knowledge_state to understand current mastery levels.\n"
            "3. Present ready courses with a brief description.\n"
            "4. For not-ready courses, explain which prerequisite concepts need strengthening and by how much.\n"
            "5. Suggest specific study actions to bridge the gaps.\n"
            "Answer in the same language as the student."
        )
    elif intent == "wellbeing":
        qa_system = (
            "You are a caring, empathetic study support assistant.\n"
            + context_block
            + "The student is expressing stress or difficulty. Respond with empathy first, then practical help.\n"
            "Approach:\n"
            "- Acknowledge their feelings warmly and normalise the difficulty\n"
            "- Call get_study_plan to review their current load\n"
            "- Suggest ONE concrete, small step they can take today (not a full overhaul)\n"
            "- Remind them that progress matters more than perfection\n"
            "- If appropriate, mention that their schedule can be adjusted\n"
            "Keep the response warm and encouraging. Answer in Vietnamese."
        )
    else:
        qa_system = (
            "You are a helpful AI study assistant.\n"
            + context_block
            + "Use tools only when the student's question requires detailed or updated data.\n"
            "Answer in the same language as the student (Vietnamese or English).\n"
            "Be warm, concise, and specific."
        )

    async def generate():
        ds_thinking = False
        qw_thinking = False
        buf = ""
        try:
            # Hold one `chat` endpoint for the whole turn (proactive + Q&A).
            async with get_pool().acquire(ROLE_CHAT) as lease:
                llm = lease.chat(temperature=0.6, streaming=True)
                proactive_agent = create_agent(llm, tools, system_prompt=proactive_system)
                qa_agent = create_agent(llm, tools, system_prompt=qa_system)

                # ── Phase 1: Proactive check (tool_call + data_updated only) ──
                async for event in proactive_agent.astream_events(
                    {"messages": [HumanMessage("Run proactive check.")]},
                    version="v2",
                    config={"recursion_limit": _PROACTIVE_LIMIT},
                ):
                    kind = event["event"]
                    if kind == "on_tool_start":
                        name = event.get("name", "")
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': name})}\n\n"
                    elif kind == "on_tool_end":
                        name = event.get("name", "")
                        if name in WRITE_TOOL_NAMES:
                            resources = WRITE_TOOL_RESOURCES.get(name, [])
                            yield f"data: {json.dumps({'type': 'data_updated', 'resources': resources})}\n\n"

                # ── Phase 2: Q&A (full streaming) ────────────────────────────
                async for event in qa_agent.astream_events(
                    {"messages": history_lc + [HumanMessage(user_input)]},
                    version="v2",
                    config={"recursion_limit": _QA_LIMIT},
                ):
                    kind = event["event"]
                    if kind == "on_tool_start":
                        name = event.get("name", "")
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': name})}\n\n"
                    elif kind == "on_tool_end":
                        name = event.get("name", "")
                        if name in WRITE_TOOL_NAMES:
                            resources = WRITE_TOOL_RESOURCES.get(name, [])
                            yield f"data: {json.dumps({'type': 'data_updated', 'resources': resources})}\n\n"
                        if name == "mark_assignment_complete":
                            from agent.weekly_planner import run_weekly_planning
                            asyncio.create_task(
                                run_weekly_planning(req.student_id, trigger="task_complete")
                            )
                    elif kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                        if reasoning:
                            ds_thinking = True
                            yield f"data: {json.dumps({'type': 'thinking', 'delta': reasoning})}\n\n"
                            continue
                        content = chunk.content
                        if not content:
                            continue
                        if ds_thinking:
                            ds_thinking = False
                            yield f"data: {json.dumps({'type': 'thinking_done'})}\n\n"
                        buf += content
                        while buf:
                            tag = _THINK_CLOSE if qw_thinking else _THINK_OPEN
                            idx = buf.find(tag)
                            if idx == -1:
                                p = _partial_tag(buf, tag)
                                emit, buf = buf[: len(buf) - p], buf[len(buf) - p :]
                                if emit:
                                    etype = "thinking" if qw_thinking else "content"
                                    yield f"data: {json.dumps({'type': etype, 'delta': emit})}\n\n"
                                break
                            before, buf = buf[:idx], buf[idx + len(tag) :]
                            if before:
                                etype = "thinking" if qw_thinking else "content"
                                yield f"data: {json.dumps({'type': etype, 'delta': before})}\n\n"
                            if qw_thinking:
                                yield f"data: {json.dumps({'type': 'thinking_done'})}\n\n"
                            qw_thinking = not qw_thinking

                if buf:
                    etype = "thinking" if qw_thinking else "content"
                    yield f"data: {json.dumps({'type': etype, 'delta': buf})}\n\n"
                if ds_thinking or qw_thinking:
                    yield f"data: {json.dumps({'type': 'thinking_done'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            print(f"[chat] {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
