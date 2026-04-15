from datetime import datetime
from pydantic import BaseModel, Field


class EmotionScores(BaseModel):
    Angry: float = 0.0
    Disgust: float = 0.0
    Fear: float = 0.0
    Happy: float = 0.0
    Sad: float = 0.0
    Surprise: float = 0.0
    Neutral: float = 0.0


class EmotionResult(BaseModel):
    emotion: str
    confidence: float
    scores: EmotionScores


class EmotionLog(BaseModel):
    id: str | None = None
    user_id: str
    session_id: str
    emotion: str
    confidence: float
    scores: EmotionScores
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmotionResponse(BaseModel):
    emotion: str
    confidence: float
    scores: EmotionScores
    suggestion: str | None = None


class EmotionHistory(BaseModel):
    logs: list[EmotionLog]
    total: int
