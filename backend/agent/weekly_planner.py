from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, get_knowledge_state_stub, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool


async def run_weekly_planning(student_id: int, trigger: str = "cron") -> None:
    ctx = await get_student_context(student_id)
    kt = await get_knowledge_state_stub(student_id)
    kt_summary = ", ".join(f"{c}: {v:.0%}" for c, v in kt.items()) if kt else "none"

    trigger_note = {
        "cron": "This is the scheduled Monday morning plan rebuild.",
        "risk_spike": "URGENT: Student's risk score spiked above threshold. Reduce session length and add more review sessions.",
        "task_complete": "Student just completed an assignment. Rebalance remaining sessions.",
        "wellbeing_relief": "WELLBEING ALERT: Student is stressed. Reduce total daily load by ~20%, prioritise rest and short review sessions over long practice sessions.",
        "data_change": "A new score or assignment was just recorded. Re-balance the week around the updated deadlines and any new weak areas.",
        "behind_schedule": "Student is falling behind on an upcoming assignment (deadline near, not started). Front-load milestone work this week so they catch up before the deadline.",
    }.get(trigger, f"Trigger: {trigger}")

    context_block = (
        f"Student: {ctx['full_name']} (ID: {student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f} | Flags: {ctx['risk_flags']}\n"
        f"Unsubmitted: {ctx['unsubmitted_count']} | Next due: day {ctx['next_due']}\n"
        f"Knowledge mastery: {kt_summary}\n"
    )

    tools = make_tools(student_id)
    system_prompt = (
        f"You are a weekly study planner. {trigger_note}\n"
        + context_block
        + "Steps:\n"
        "1. Call get_assignments to check all upcoming deadlines and scores.\n"
        "2. Call get_study_plan to review the current session list.\n"
        "3. Call update_study_plan with a complete rebuilt week (Mon–Sun).\n"
        "   Rules:\n"
        "   - 2–4 sessions per day, 20–120 min each\n"
        "   - Include spaced repetition for concepts with mastery < 0.7\n"
        "   - Prioritise upcoming deadlines (within 7 days)\n"
        "   - If risk_score > 0.6: reduce session length; add more review sessions\n"
        "   - Spread assignment work across multiple days, not just the deadline day\n"
        "4. Call create_reminder (type='reminder') with a concise weekly overview: "
        "key deadlines, today's focus session, and an encouraging note.\n"
        "Answer in Vietnamese."
    )

    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.6), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage("Rebuild this week's study plan.")]},
                config={"recursion_limit": 18},
            )
        print(f"[weekly_planner] Completed for student {student_id} (trigger={trigger})")
    except Exception as e:
        print(f"[weekly_planner] Error for student {student_id}: {type(e).__name__}: {e}")
