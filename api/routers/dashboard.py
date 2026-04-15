import csv
import io
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from api.core.dependencies import get_teacher_or_admin
from api.services.dashboard import get_class_emotion_summary, export_emotion_data, get_student_detail

router = APIRouter(prefix="/dashboard", tags=["Teacher Dashboard"])


@router.get("/summary")
async def class_summary(
    session_id: str | None = None,
    hours: int = Query(default=24, ge=1, le=720),
    user: dict = Depends(get_teacher_or_admin),
):
    return await get_class_emotion_summary(
        teacher_id=user["id"],
        session_id=session_id,
        hours=hours,
    )


@router.get("/export")
async def export_data(
    format: str = Query(default="json", pattern="^(json|csv)$"),
    session_id: str | None = None,
    hours: int = Query(default=24, ge=1, le=720),
    user: dict = Depends(get_teacher_or_admin),
):
    data = await export_emotion_data(
        teacher_id=user["id"],
        session_id=session_id,
        hours=hours,
    )

    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=emotion_report.csv"},
        )

    return StreamingResponse(
        iter([json.dumps(data, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=emotion_report.json"},
    )


@router.get("/student/{student_id}")
async def student_detail(
    student_id: str,
    hours: int = Query(default=24, ge=1, le=720),
    user: dict = Depends(get_teacher_or_admin),
):
    data = await get_student_detail(student_id=student_id, hours=hours)
    if data is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")
    return data
