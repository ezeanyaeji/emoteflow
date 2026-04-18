from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId

from core.database import get_db
from core.dependencies import get_teacher_or_admin
from models.assignment import AssignStudents, AssignmentResponse
from models.user import UserRole
from services.assignment import (
    get_assigned_student_ids,
    assign_students,
    add_students,
    remove_students,
)

router = APIRouter(prefix="/assignments", tags=["Teacher-Student Assignments"])


@router.get("/my-students", response_model=AssignmentResponse)
async def list_my_students(user: dict = Depends(get_teacher_or_admin)):
    """List the student IDs currently assigned to this teacher."""
    ids = await get_assigned_student_ids(user["id"])
    student_ids = ids or []
    return AssignmentResponse(
        teacher_id=user["id"],
        student_ids=student_ids,
        total=len(student_ids),
    )


@router.put("/my-students", response_model=AssignmentResponse)
async def set_my_students(
    body: AssignStudents,
    user: dict = Depends(get_teacher_or_admin),
):
    """Replace the full list of assigned students."""
    count = await assign_students(user["id"], body.student_ids)
    return AssignmentResponse(
        teacher_id=user["id"],
        student_ids=body.student_ids,
        total=count,
    )


@router.post("/my-students", status_code=status.HTTP_201_CREATED)
async def add_my_students(
    body: AssignStudents,
    user: dict = Depends(get_teacher_or_admin),
):
    """Add students to the teacher's list."""
    added = await add_students(user["id"], body.student_ids)
    return {"added": added}


@router.delete("/my-students")
async def remove_my_students(
    body: AssignStudents,
    user: dict = Depends(get_teacher_or_admin),
):
    """Remove students from the teacher's list."""
    removed = await remove_students(user["id"], body.student_ids)
    return {"removed": removed}


@router.get("/available-students")
async def available_students(
    search: str = Query(default="", description="Filter by name or email"),
    user: dict = Depends(get_teacher_or_admin),
):
    """List all students (for the teacher to pick from)."""
    db = get_db()
    query = {"role": UserRole.STUDENT.value}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    cursor = db.users.find(query).sort("last_name", 1).limit(100)
    students = []
    async for u in cursor:
        students.append({
            "id": str(u["_id"]),
            "email": u["email"],
            "first_name": u["first_name"],
            "last_name": u["last_name"],
        })
    return {"students": students}
