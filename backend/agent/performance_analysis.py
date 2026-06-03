from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, get_knowledge_state_stub, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool
from agent.student_skills import get_skill_gaps


async def run_performance_analysis(student_id: int) -> dict:
    """Orchestrator O3 — synthesise KT state, VLE, and scores into a performance snapshot."""
    ctx = await get_student_context(student_id)
    kt = await get_knowledge_state_stub(student_id)
    gaps = await get_skill_gaps(student_id, threshold=0.6)
    kt_summary = ", ".join(f"{c}: {v:.0%}" for c, v in kt.items()) if kt else "none"

    context_block = (
        f"Student: {ctx['full_name']} (ID: {student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f} | Flags: {ctx['risk_flags']}\n"
        f"Concept mastery: {kt_summary}\n"
        f"Concepts below 60%: {gaps or 'none'}\n"
    )

    tools = make_tools(student_id)
    system_prompt = (
        "You are a Performance Analysis Agent (Orchestrator O3).\n"
        + context_block
        + "Steps:\n"
        "1. Call get_student_profile to review VLE engagement, scores, and prerequisite gaps.\n"
        "2. Call get_knowledge_state to see current mastery per concept.\n"
        "3. Call get_assignments to check assessment scores and identify low-scoring items.\n"
        "4. Synthesise findings:\n"
        "   - Identify the 2–3 weakest concepts (mastery < 0.6)\n"
        "   - Assess VLE trend (active/declining/inactive based on weekly_clicks)\n"
        "   - Identify lowest-scoring assessments\n"
        "   - Determine the single highest-impact next action\n"
        "5. Call save_study_note (subject='Phân tích hiệu suất') with a structured summary.\n"
        "6. If risk_score > 0.6 or any concept mastery < 0.4: call create_reminder "
        "(type='intervention') alerting the student to their top weakness and recommended action.\n"
        "Be concise and specific. Answer in Vietnamese."
    )

    result = {"weak_concepts": gaps, "vle_trend": "unknown", "next_action": ""}
    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.4), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage("Run performance analysis.")]},
                config={"recursion_limit": 21},
            )
        result["next_action"] = "See saved study note"
        print(f"[performance_analysis] Completed for student {student_id}")
    except Exception as e:
        print(f"[performance_analysis] Error for student {student_id}: {type(e).__name__}: {e}")

    return result
