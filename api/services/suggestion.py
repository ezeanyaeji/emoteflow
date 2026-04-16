from models.suggestion import Suggestion

# Rule-based emotion → suggestion mapping (from app_documentation.md)
SUGGESTION_RULES: dict[str, list[Suggestion]] = {
    "Happy": [
        Suggestion(
            emotion="Happy",
            action="Continue current activity or try a harder challenge",
            description="Student is engaged and positive. Increase difficulty to maintain flow state.",
            category="challenge",
        ),
        Suggestion(
            emotion="Happy",
            action="Introduce group collaboration exercise",
            description="Leverage positive mood for peer learning.",
            category="interactive",
        ),
    ],
    "Sad": [
        Suggestion(
            emotion="Sad",
            action="Take a short break",
            description="Student may be overwhelmed. A brief pause can help reset focus.",
            category="break",
        ),
        Suggestion(
            emotion="Sad",
            action="Revisit simpler material",
            description="Go back to a topic the student previously understood well to rebuild confidence.",
            category="review",
        ),
    ],
    "Fear": [
        Suggestion(
            emotion="Fear",
            action="Review the last concept with guided examples",
            description="Student may be anxious about the material. Provide step-by-step guidance.",
            category="review",
        ),
        Suggestion(
            emotion="Fear",
            action="Offer encouragement and reassurance",
            description="Remind the student that mistakes are part of learning.",
            category="calming",
        ),
    ],
    "Angry": [
        Suggestion(
            emotion="Angry",
            action="Pause learning and try a calming activity",
            description="Student is frustrated. A short breathing exercise or change of pace can help.",
            category="calming",
        ),
        Suggestion(
            emotion="Angry",
            action="Switch to a different topic",
            description="Redirect attention to reduce frustration with current material.",
            category="interactive",
        ),
    ],
    "Surprise": [
        Suggestion(
            emotion="Surprise",
            action="Explore the surprising concept further",
            description="Student encountered something unexpected. Capitalize on curiosity.",
            category="challenge",
        ),
    ],
    "Disgust": [
        Suggestion(
            emotion="Disgust",
            action="Change activity or presentation style",
            description="Student may be disengaged with the current format. Try a different approach.",
            category="interactive",
        ),
    ],
    "Neutral": [
        Suggestion(
            emotion="Neutral",
            action="Switch to interactive exercises",
            description="Student is neither engaged nor disengaged. Increase interactivity to boost engagement.",
            category="interactive",
        ),
        Suggestion(
            emotion="Neutral",
            action="Ask a thought-provoking question",
            description="Stimulate critical thinking to shift from passive to active learning.",
            category="challenge",
        ),
    ],
}


def get_suggestion_for_emotion(emotion: str) -> Suggestion | None:
    import random
    suggestions = SUGGESTION_RULES.get(emotion)
    if not suggestions:
        return None
    return random.choice(suggestions)


def get_all_suggestions_for_emotion(emotion: str) -> list[Suggestion]:
    return SUGGESTION_RULES.get(emotion, [])
