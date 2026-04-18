"""Teacher ↔ student assignment service.

Each document in the `assignments` collection:
    { teacher_id: str, student_id: str }
"""

from core.database import get_db


async def get_assigned_student_ids(teacher_id: str) -> list[str] | None:
    """Return list of student IDs assigned to this teacher, or None if no
    assignments exist (which means the teacher sees all students — backwards
    compatible)."""
    db = get_db()
    cursor = db.assignments.find({"teacher_id": teacher_id})
    ids = []
    async for doc in cursor:
        ids.append(doc["student_id"])
    return ids if ids else None


async def assign_students(teacher_id: str, student_ids: list[str]) -> int:
    """Replace the teacher's student list with the provided IDs."""
    db = get_db()
    # Remove existing assignments for this teacher
    await db.assignments.delete_many({"teacher_id": teacher_id})
    if not student_ids:
        return 0
    docs = [{"teacher_id": teacher_id, "student_id": sid} for sid in student_ids]
    result = await db.assignments.insert_many(docs)
    return len(result.inserted_ids)


async def add_students(teacher_id: str, student_ids: list[str]) -> int:
    """Add students to the teacher's list (skip duplicates)."""
    db = get_db()
    added = 0
    for sid in student_ids:
        existing = await db.assignments.find_one(
            {"teacher_id": teacher_id, "student_id": sid}
        )
        if not existing:
            await db.assignments.insert_one(
                {"teacher_id": teacher_id, "student_id": sid}
            )
            added += 1
    return added


async def remove_students(teacher_id: str, student_ids: list[str]) -> int:
    """Remove students from the teacher's list."""
    db = get_db()
    removed = 0
    for sid in student_ids:
        result = await db.assignments.delete_one(
            {"teacher_id": teacher_id, "student_id": sid}
        )
        removed += result.deleted_count
    return removed
