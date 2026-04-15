from fastapi import APIRouter, Depends, Query
from bson import ObjectId

from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models.suggestion import Suggestion, SuggestionFeedback, SuggestionHistory, SuggestionLog
from api.services.suggestion import get_all_suggestions_for_emotion

router = APIRouter(prefix="/suggestion", tags=["Suggestions"])


@router.get("/rules/{emotion}", response_model=list[Suggestion])
async def get_rules(emotion: str, _user: dict = Depends(get_current_user)):
    return get_all_suggestions_for_emotion(emotion.capitalize())


@router.get("/history", response_model=SuggestionHistory)
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

    total = await db.suggestions.count_documents(query)
    cursor = db.suggestions.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    logs = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        logs.append(SuggestionLog(**doc))

    return SuggestionHistory(logs=logs, total=total)


@router.post("/feedback")
async def submit_feedback(
    data: SuggestionFeedback,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    result = await db.suggestions.update_one(
        {"_id": ObjectId(data.suggestion_id), "user_id": user["id"]},
        {"$set": {"feedback": data.feedback}},
    )
    if result.matched_count == 0:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    return {"message": "Feedback submitted"}
