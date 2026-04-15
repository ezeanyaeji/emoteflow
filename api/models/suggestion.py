from datetime import datetime
from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    emotion: str
    action: str
    description: str
    category: str  # e.g. "break", "challenge", "review", "interactive", "calming"


class SuggestionLog(BaseModel):
    id: str | None = None
    user_id: str
    session_id: str
    emotion: str
    suggestion: Suggestion
    feedback: str | None = None  # student feedback on the suggestion
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuggestionFeedback(BaseModel):
    suggestion_id: str
    feedback: str = Field(..., max_length=500)


class SuggestionHistory(BaseModel):
    logs: list[SuggestionLog]
    total: int
