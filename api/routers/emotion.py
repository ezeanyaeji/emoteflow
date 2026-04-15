import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from bson import ObjectId

from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models.emotion import EmotionLog, EmotionResponse, EmotionHistory
from api.services.emotion import predict_emotion
from api.services.suggestion import get_suggestion_for_emotion

router = APIRouter(prefix="/emotion", tags=["Emotion Recognition"])


@router.post("/predict", response_model=EmotionResponse)
async def predict(
    file: UploadFile = File(...),
    session_id: str = Query(default=None, description="Learning session ID"),
    user: dict = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    image_bytes = await file.read()
    if len(image_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too large (max 5MB)",
        )

    try:
        result = predict_emotion(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Get suggestion for this emotion
    suggestion = get_suggestion_for_emotion(result["emotion"])

    # Log to database
    db = get_db()
    log = EmotionLog(
        user_id=user["id"],
        session_id=session_id or str(uuid.uuid4()),
        emotion=result["emotion"],
        confidence=result["confidence"],
        scores=result["scores"],
        timestamp=datetime.now(timezone.utc),
    )
    log_doc = log.model_dump()
    insert_result = await db.emotions.insert_one(log_doc)

    # Also log the suggestion
    if suggestion:
        suggestion_doc = {
            "user_id": user["id"],
            "session_id": log.session_id,
            "emotion": result["emotion"],
            "suggestion": suggestion.model_dump(),
            "timestamp": datetime.now(timezone.utc),
        }
        await db.suggestions.insert_one(suggestion_doc)

    return EmotionResponse(
        emotion=result["emotion"],
        confidence=result["confidence"],
        scores=result["scores"],
        suggestion=suggestion.action if suggestion else None,
    )


@router.get("/history", response_model=EmotionHistory)
async def get_history(
    session_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    db = get_db()
    query = {"user_id": user["id"]}
    if session_id:
        query["session_id"] = session_id

    total = await db.emotions.count_documents(query)
    cursor = db.emotions.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    logs = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        logs.append(EmotionLog(**doc))

    return EmotionHistory(logs=logs, total=total)
