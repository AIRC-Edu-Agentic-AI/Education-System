from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool


async def run_daily_planning(student_id: int) -> None:
    ctx = await get_student_context(student_id)
    context_block = (
        f"Student: {ctx['full_name']} (ID: {student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f} | Flags: {ctx['risk_flags']}\n"
        f"Unsubmitted: {ctx['unsubmitted_count']} | Next due: day {ctx['next_due']}\n"
    )

    tools = make_tools(student_id)
    system_prompt = (
        "You are a daily planning assistant. Your job runs at 08:00 each morning.\n"
        + context_block
        + "Steps:\n"
        "1. Call get_assignments to see upcoming deadlines.\n"
        "2. Call get_study_plan to review existing sessions.\n"
        "3. If sessions are missing, stale, or misaligned with deadlines, "
        "call update_study_plan with a refreshed weekly session list.\n"
        "4. Always call create_reminder with a concise morning briefing: "
        "today's top priority, one study session to do, and an encouraging note.\n"
        "Keep sessions realistic: 2–4 per day, 20–120 min each. "
        "Prioritise upcoming deadlines and spaced repetition. "
        "Answer in Vietnamese."
    )

    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.6), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage("Good morning — please build today's plan and send the briefing.")]},
                config={"recursion_limit": 15},
            )
        print(f"[daily_planner] Completed for student {student_id}")
    except Exception as e:
        print(f"[daily_planner] Error for student {student_id}: {type(e).__name__}: {e}")
