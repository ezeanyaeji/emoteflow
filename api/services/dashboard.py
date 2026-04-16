from datetime import datetime, timedelta, timezone

from bson import ObjectId

from core.database import get_db


async def get_class_emotion_summary(
    teacher_id: str,
    session_id: str | None = None,
    hours: int = 24,
) -> dict:
    db = get_db()

    # Get all students (teacher sees all students' data)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    match_stage: dict = {"timestamp": {"$gte": since}}
    if session_id:
        match_stage["session_id"] = session_id

    # Aggregate emotion distribution
    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$emotion",
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"},
            }
        },
        {"$sort": {"count": -1}},
    ]
    distribution = {}
    async for doc in db.emotions.aggregate(pipeline):
        distribution[doc["_id"]] = {
            "count": doc["count"],
            "avg_confidence": round(doc["avg_confidence"], 4),
        }

    # Emotion timeline (hourly buckets)
    timeline_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "hour": {"$dateToString": {"format": "%Y-%m-%dT%H:00:00Z", "date": "$timestamp"}},
                    "emotion": "$emotion",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.hour": 1}},
    ]
    timeline = {}
    async for doc in db.emotions.aggregate(timeline_pipeline):
        hour = doc["_id"]["hour"]
        emotion = doc["_id"]["emotion"]
        if hour not in timeline:
            timeline[hour] = {}
        timeline[hour][emotion] = doc["count"]

    # Per-student summary
    student_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$user_id",
                "total_logs": {"$sum": 1},
                "dominant_emotion": {"$first": "$emotion"},  # most recent
                "last_seen": {"$max": "$timestamp"},
            }
        },
    ]
    students = []
    async for doc in db.emotions.aggregate(student_pipeline):
        # Look up student name
        user = await db.users.find_one({"_id": ObjectId(doc["_id"])})
        name = f"{user['first_name']} {user['last_name']}" if user else "Unknown"
        students.append({
            "user_id": doc["_id"],
            "name": name,
            "total_logs": doc["total_logs"],
            "dominant_emotion": doc["dominant_emotion"],
            "last_seen": doc["last_seen"].isoformat(),
        })

    total_logs = sum(d["count"] for d in distribution.values())

    return {
        "period_hours": hours,
        "total_emotion_logs": total_logs,
        "unique_students": len(students),
        "emotion_distribution": distribution,
        "timeline": timeline,
        "students": students,
    }


async def export_emotion_data(
    teacher_id: str,
    session_id: str | None = None,
    hours: int = 24,
) -> list[dict]:
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query: dict = {"timestamp": {"$gte": since}}
    if session_id:
        query["session_id"] = session_id

    rows = []
    async for doc in db.emotions.find(query).sort("timestamp", 1):
        rows.append({
            "user_id": doc["user_id"],
            "session_id": doc["session_id"],
            "emotion": doc["emotion"],
            "confidence": doc["confidence"],
            "timestamp": doc["timestamp"].isoformat(),
        })
    return rows


async def get_student_detail(student_id: str, hours: int = 24) -> dict | None:
    db = get_db()

    # Get student info
    user = await db.users.find_one({"_id": ObjectId(student_id)})
    if not user:
        return None

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    match_stage = {"user_id": student_id, "timestamp": {"$gte": since}}

    # Emotion distribution
    emo_pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$emotion", "count": {"$sum": 1}, "avg_confidence": {"$avg": "$confidence"}}},
        {"$sort": {"count": -1}},
    ]
    emotion_distribution = {}
    async for doc in db.emotions.aggregate(emo_pipeline):
        emotion_distribution[doc["_id"]] = {
            "count": doc["count"],
            "avg_confidence": round(doc["avg_confidence"], 4),
        }

    # Timeline (hourly)
    timeline_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {
                    "hour": {"$dateToString": {"format": "%Y-%m-%dT%H:00:00Z", "date": "$timestamp"}},
                    "emotion": "$emotion",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.hour": 1}},
    ]
    timeline = {}
    async for doc in db.emotions.aggregate(timeline_pipeline):
        hour = doc["_id"]["hour"]
        emotion = doc["_id"]["emotion"]
        if hour not in timeline:
            timeline[hour] = {}
        timeline[hour][emotion] = doc["count"]

    # Recent emotions (last 20)
    recent = []
    async for doc in db.emotions.find(match_stage).sort("timestamp", -1).limit(20):
        recent.append({
            "emotion": doc["emotion"],
            "confidence": round(doc["confidence"], 4),
            "timestamp": doc["timestamp"].isoformat(),
        })

    total_logs = sum(d["count"] for d in emotion_distribution.values())
    dominant = max(emotion_distribution, key=lambda e: emotion_distribution[e]["count"]) if emotion_distribution else "N/A"

    return {
        "student": {
            "id": str(user["_id"]),
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
        },
        "period_hours": hours,
        "total_logs": total_logs,
        "dominant_emotion": dominant,
        "emotion_distribution": emotion_distribution,
        "timeline": timeline,
        "recent_emotions": recent,
    }


async def get_admin_stats(hours: int = 24) -> dict:
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # User counts by role
    role_pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}}
    ]
    user_counts = {}
    async for doc in db.users.aggregate(role_pipeline):
        user_counts[doc["_id"]] = doc["count"]

    total_users = sum(user_counts.values())

    # Emotion stats for the period
    match_stage = {"timestamp": {"$gte": since}}
    total_emotions = await db.emotions.count_documents(match_stage)

    # Emotion distribution
    emo_pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$emotion", "count": {"$sum": 1}, "avg_confidence": {"$avg": "$confidence"}}},
        {"$sort": {"count": -1}},
    ]
    emotion_distribution = {}
    async for doc in db.emotions.aggregate(emo_pipeline):
        emotion_distribution[doc["_id"]] = {
            "count": doc["count"],
            "avg_confidence": round(doc["avg_confidence"], 4),
        }

    # Active students (those who logged emotions in the period)
    active_pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"},
    ]
    active_result = [doc async for doc in db.emotions.aggregate(active_pipeline)]
    active_students = active_result[0]["count"] if active_result else 0

    # Recent registrations
    recent_users_cursor = db.users.find().sort("created_at", -1).limit(10)
    recent_users = []
    async for u in recent_users_cursor:
        recent_users.append({
            "id": str(u["_id"]),
            "email": u["email"],
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "role": u["role"],
            "created_at": u["created_at"].isoformat(),
        })

    # Emotion timeline (hourly)
    timeline_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%dT%H:00:00Z", "date": "$timestamp"}},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    timeline = []
    async for doc in db.emotions.aggregate(timeline_pipeline):
        timeline.append({"hour": doc["_id"], "count": doc["count"]})

    return {
        "period_hours": hours,
        "total_users": total_users,
        "user_counts": user_counts,
        "total_emotion_logs": total_emotions,
        "active_students": active_students,
        "emotion_distribution": emotion_distribution,
        "timeline": timeline,
        "recent_users": recent_users,
    }
