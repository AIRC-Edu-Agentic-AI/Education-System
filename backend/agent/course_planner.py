from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, get_knowledge_state_stub, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool


async def run_course_planning(student_id: int, trigger: str = "midpoint") -> None:
    ctx = await get_student_context(student_id)
    kt = await get_knowledge_state_stub(student_id)
    kt_summary = ", ".join(f"{c}: {v:.0%}" for c, v in kt.items()) if kt else "none"

    trigger_desc = {
        "midpoint": "Student has reached the midpoint of their module (week 15/30).",
        "assessment_shock": "Student received a low score (<50%) on a recent assessment.",
        "enrollment": "Student has just enrolled in a new module.",
        "orchestrated": "Risk Intervention Agent has requested a course-level assessment.",
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
        f"You are a course planning advisor. {trigger_desc}\n"
        + context_block
        + "Steps:\n"
        "1. Call get_student_profile to review enrollments, VLE engagement, and prerequisite gaps.\n"
        "2. Call get_assignments to see all assessment scores and upcoming deadlines.\n"
        "3. Analyse the student's trajectory:\n"
        "   - Are they on pace to pass? Which assessments are at risk?\n"
        "   - Which prerequisite gaps are blocking progress?\n"
        "   - Is the VLE engagement sufficient?\n"
        "4. Call create_reminder (type='intervention') with clear, actionable semester-level advice: "
        "top 2–3 priorities, specific study focus areas, and a realistic plan to improve.\n"
        "5. Call save_study_note to record a structured course progress summary "
        "(subject='Kế hoạch học kỳ', include trajectory assessment and recommended actions).\n"
        "Be direct and specific — name the modules, assessment types, and concepts explicitly.\n"
        "Answer in Vietnamese."
    )

    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.6), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage("Assess my course trajectory and give me a plan.")]},
                config={"recursion_limit": 18},
            )
        print(f"[course_planner] Completed for student {student_id} (trigger={trigger})")
    except Exception as e:
        print(f"[course_planner] Error for student {student_id}: {type(e).__name__}: {e}")
