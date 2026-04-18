from pydantic import BaseModel


class AssignStudents(BaseModel):
    student_ids: list[str]


class AssignmentResponse(BaseModel):
    teacher_id: str
    student_ids: list[str]
    total: int
