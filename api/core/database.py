from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


def _build_mongo_uri() -> str:
    """Build a MongoDB URI with properly escaped credentials."""
    if settings.MONGODB_USER and settings.MONGODB_PASSWORD:
        user = quote_plus(settings.MONGODB_USER)
        password = quote_plus(settings.MONGODB_PASSWORD)
        return f"mongodb+srv://{user}:{password}@{settings.MONGODB_HOST}"
    # Fallback for local MongoDB without auth
    return f"mongodb://{settings.MONGODB_HOST}"


async def connect_db():
    global client, db
    mongo_uri = _build_mongo_uri()
    client = AsyncIOMotorClient(mongo_uri)
    db = client[settings.MONGODB_DB_NAME]
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.emotions.create_index([("user_id", 1), ("timestamp", -1)])
    await db.suggestions.create_index([("user_id", 1), ("timestamp", -1)])
    await db.assignments.create_index([("teacher_id", 1), ("student_id", 1)], unique=True)
    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_db():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    return db
