from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, get_knowledge_state_stub, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool
from agent.student_skills import get_skill_gaps


async def run_progress_report(student_id: int) -> None:
    """Generate a weekly progress report and push a summary notification."""
    ctx = await get_student_context(student_id)
    kt = await get_knowledge_state_stub(student_id)
    gaps = await get_skill_gaps(student_id, threshold=0.6)
    kt_summary = ", ".join(f"{c}: {v:.0%}" for c, v in kt.items()) if kt else "none"

    context_block = (
        f"Student: {ctx['full_name']} (ID: {student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f}\n"
        f"Concept mastery: {kt_summary}\n"
        f"Weak concepts (< 60%): {gaps or 'none'}\n"
    )

    tools = make_tools(student_id)
    system_prompt = (
        "You are a Progress Report Agent. It is Sunday evening — time for the weekly review.\n"
        + context_block
        + "Steps:\n"
        "1. Call get_assignments to see what was submitted this week and upcoming deadlines.\n"
        "2. Call get_study_plan to see this week's sessions.\n"
        "3. Call get_knowledge_state to identify mastery gains.\n"
        "4. Write a weekly report (in Vietnamese) covering:\n"
        "   - Accomplishments: submissions, sessions completed, mastery improvements\n"
        "   - Upcoming: deadlines and priorities for next week\n"
        "   - One specific encouragement based on progress\n"
        "5. Call create_reminder (type='progress_report') with the report as the body.\n"
        "Keep it concise: 3–5 bullet points max per section."
    )

    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.5), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage("Generate the weekly progress report.")]},
                config={"recursion_limit": 18},
            )
        print(f"[progress_report] Completed for student {student_id}")
    except Exception as e:
        print(f"[progress_report] Error for student {student_id}: {type(e).__name__}: {e}")
