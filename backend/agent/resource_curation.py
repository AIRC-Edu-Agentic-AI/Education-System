from db.mock_data import MOCK_RESOURCES
from db.mongodb import get_db


async def curate_resources(student_id: int, concepts: list[str]) -> list[dict]:
    """Return top resources matching the given concepts, from DB or mock."""
    db = get_db()

    if db is not None:
        matched: list[dict] = []
        for concept in concepts:
            cursor = db.resources.find(
                {
                    "student_id": student_id,
                    "$or": [
                        {"title": {"$regex": concept, "$options": "i"}},
                        {"subject": {"$regex": concept, "$options": "i"}},
                    ],
                }
            ).limit(3)
            docs = await cursor.to_list(length=3)
            for d in docs:
                d.pop("_id", None)
            matched.extend(docs)
        return matched[:5]

    # Mock fallback: keyword match against MOCK_RESOURCES
    matched = []
    for concept in concepts:
        cl = concept.lower()
        for r in MOCK_RESOURCES:
            title_match = cl in r.get("title", "").lower()
            module_match = cl in r.get("module", "").lower()
            if title_match or module_match:
                matched.append(r)
    # Deduplicate by title and cap at 5
    seen: set[str] = set()
    unique: list[dict] = []
    for r in matched:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)
    # Fallback: return first 3 mock resources if no keyword match
    return unique[:5] if unique else MOCK_RESOURCES[:3]
