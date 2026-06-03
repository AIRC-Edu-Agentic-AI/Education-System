"""Reactive agent — runs when a new score or assignment is received.

Produces a tailored notification (change summary + recommended next action),
then triggers a weekly replan so the study plan reflects the new data.
"""
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool


async def react_to_assessment_change(
    student_id: int, summary: str, replan: bool = True
) -> None:
    """`summary` is a short human-readable description of what changed, e.g.
    "Điểm mới: TMA — Đại số Tuyến tính: 65%" or
    "Bài tập mới: CMA — Phân tích Dữ liệu (hạn ngày 60, 20%)"."""
    ctx = await get_student_context(student_id)
    context_block = (
        f"Student: {ctx['full_name']} (ID: {student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f}\n"
        f"Unsubmitted: {ctx['unsubmitted_count']} | Next due: day {ctx['next_due']}\n"
    )

    tools = make_tools(student_id)
    system_prompt = (
        "You are a reactive study advisor. A change just occurred in the student's record:\n"
        f"  >>> {summary} <<<\n"
        + context_block
        + "Steps:\n"
        "1. (Optional) Call get_assignments and/or get_knowledge_state for context.\n"
        "2. Call create_reminder(type='assessment_update') with:\n"
        "   - title: a short line naming the change (mention the module).\n"
        "   - body: the SINGLE most important next action, concrete and specific "
        "(1–2 sentences). For a low score, focus on remediation; for a good score, "
        "reinforce momentum; for a new assignment, give a starting step before the deadline.\n"
        "Do NOT repeat tool calls. Answer in Vietnamese."
    )

    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.5), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage(f"React to: {summary}")]},
                config={"recursion_limit": 10},
            )
        print(f"[assessment_reaction] Notified student {student_id}: {summary}")
    except Exception as e:
        print(f"[assessment_reaction] Error for student {student_id}: {type(e).__name__}: {e}")

    if replan:
        from agent.weekly_planner import run_weekly_planning
        await run_weekly_planning(student_id, trigger="data_change")
