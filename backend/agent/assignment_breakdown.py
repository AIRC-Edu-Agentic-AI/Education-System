from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import get_student_context, make_tools
from agent.llm_pool import ROLE_AGENT, get_pool


async def run_breakdown(student_id: int, id_assessment: int) -> None:
    """Generate and store milestones for a specific assessment."""
    ctx = await get_student_context(student_id)
    context_block = (
        f"Student: {ctx['full_name']} (ID: {student_id})\n"
        f"Module: {ctx['module']} | Risk: tier {ctx['risk_tier']}, "
        f"score {ctx['risk_score']:.2f}\n"
        f"Next due: day {ctx['next_due']}\n"
    )

    tools = make_tools(student_id)
    system_prompt = (
        "You are an Assignment Breakdown Agent that creates study milestones.\n"
        + context_block
        + f"Target assessment ID: {id_assessment}\n\n"
        "Steps:\n"
        "1. Call get_assignments to find the target assessment — get its title, type, due_date, and weight.\n"
        "2. Call get_knowledge_state to understand which related concepts need more preparation.\n"
        "3. Generate 3–5 milestones that break down the work into realistic steps.\n"
        "   Milestone rules:\n"
        "   - Each milestone needs: id (m1, m2...), title (Vietnamese), due_offset_days (negative = before due date), status='pending'\n"
        "   - Space milestones realistically: reading (-14d), analysis (-7d), drafting (-3d), submission (0d)\n"
        "   - First milestone should already be 'in_progress' if due date is approaching\n"
        "   - For high-weight assessments (>20%), add an extra review step\n"
        f"4. Call break_down_assignment(id_assessment={id_assessment}, milestones=[...]) to store them.\n"
        "Answer in Vietnamese."
    )

    try:
        async with get_pool().acquire(ROLE_AGENT) as lease:
            agent = create_agent(
                lease.chat(temperature=0.5), tools, system_prompt=system_prompt)
            await agent.ainvoke(
                {"messages": [HumanMessage(f"Break down assessment {id_assessment} into milestones.")]},
                config={"recursion_limit": 12},
            )
        print(f"[assignment_breakdown] Completed for assessment {id_assessment}")
    except Exception as e:
        print(f"[assignment_breakdown] Error: {type(e).__name__}: {e}")
