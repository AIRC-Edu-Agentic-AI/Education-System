from datetime import datetime, timezone

from agent.base import update_mastery, get_knowledge_state_stub
from db.mock_data import MOCK_KNOWLEDGE_STATES
from db.mongodb import get_db


async def run_skills_update(
    student_id: int,
    concept: str,
    evidence_type: str,
    score: float,
) -> None:
    """Update mastery for a concept after a learning event. Single gateway for all KT writes."""
    db = get_db()
    if db is None:
        print(f"[student_skills] Mock mode — would update '{concept}' ({evidence_type}, {score:.2f})")
        return

    existing = await db.knowledge_states.find_one({"student_id": student_id})
    states = existing.get("states", {}) if existing else {}
    current = states.get(concept, {}).get("mastery", 0.5)
    new_mastery = update_mastery(current, evidence_type, score)
    states[concept] = {
        "mastery": new_mastery,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "evidence_count": states.get(concept, {}).get("evidence_count", 0) + 1,
    }
    await db.knowledge_states.update_one(
        {"student_id": student_id},
        {"$set": {"states": states}},
        upsert=True,
    )
    print(f"[student_skills] Updated '{concept}': {current:.2f} → {new_mastery:.2f}")


async def get_skill_gaps(student_id: int, threshold: float = 0.5) -> list[str]:
    """Return list of concepts where mastery is below threshold."""
    states = await get_knowledge_state_stub(student_id)
    return [concept for concept, mastery in states.items() if mastery < threshold]
