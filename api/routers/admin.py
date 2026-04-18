from fastapi import APIRouter, HTTPException, status, Depends, Query

from models.user import CreateTeacher, UserResponse, UserRole
from models.assignment import AssignStudents, AssignmentResponse
from services.auth import register_user
from services.assignment import get_assigned_student_ids, assign_students
from core.dependencies import get_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/teachers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(data: CreateTeacher, user: dict = Depends(get_admin)):
    teacher = await register_user(data, role=UserRole.TEACHER)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return UserResponse(
        id=teacher["id"],
        email=teacher["email"],
        first_name=teacher["first_name"],
        last_name=teacher["last_name"],
        role=teacher["role"],
        consent_camera=teacher.get("consent_camera", False),
        created_at=teacher["created_at"],
    )


@router.get("/users")
async def list_users(
    role: UserRole | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(get_admin),
):
    from core.database import get_db

    db = get_db()
    query = {}
    if role:
        query["role"] = role.value

    total = await db.users.count_documents(query)
    cursor = db.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
    users = []
    async for u in cursor:
        users.append({
            "id": str(u["_id"]),
            "email": u["email"],
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "role": u["role"],
            "consent_camera": u.get("consent_camera", False),
            "created_at": u["created_at"].isoformat(),
        })
    return {"total": total, "users": users}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, user: dict = Depends(get_admin)):
    from bson import ObjectId
    from core.database import get_db

    db = get_db()
    if user_id == user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/stats")
async def admin_stats(
    hours: int = Query(default=24, ge=1, le=720),
    user: dict = Depends(get_admin),
):
    from services.dashboard import get_admin_stats
    return await get_admin_stats(hours=hours)


# ── Teacher-Student Assignments (admin-managed) ──────────────────────────────

@router.get("/assignments/{teacher_id}", response_model=AssignmentResponse)
async def get_teacher_assignments(teacher_id: str, user: dict = Depends(get_admin)):
    """Admin views which students are assigned to a teacher."""
    ids = await get_assigned_student_ids(teacher_id)
    student_ids = ids or []
    return AssignmentResponse(
        teacher_id=teacher_id,
        student_ids=student_ids,
        total=len(student_ids),
    )


@router.put("/assignments/{teacher_id}", response_model=AssignmentResponse)
async def set_teacher_assignments(
    teacher_id: str,
    body: AssignStudents,
    user: dict = Depends(get_admin),
):
    """Admin sets the full student list for a teacher."""
    from core.database import get_db
    from bson import ObjectId

    db = get_db()
    teacher = await db.users.find_one({"_id": ObjectId(teacher_id)})
    if not teacher or teacher["role"] not in [UserRole.TEACHER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    count = await assign_students(teacher_id, body.student_ids)
    return AssignmentResponse(
        teacher_id=teacher_id,
        student_ids=body.student_ids,
        total=count,
    )
