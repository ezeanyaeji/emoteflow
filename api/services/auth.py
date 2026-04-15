from bson import ObjectId

from api.core.database import get_db
from api.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from api.models.user import UserRegister, UserInDB, UserRole


async def register_user(data: UserRegister, role: UserRole = UserRole.STUDENT) -> dict:
    db = get_db()

    existing = await db.users.find_one({"email": data.email})
    if existing:
        return None  # email already taken

    user_doc = UserInDB(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=role,
    ).model_dump()

    result = await db.users.insert_one(user_doc)
    user_doc["id"] = str(result.inserted_id)
    return user_doc


async def authenticate_user(email: str, password: str) -> dict | None:
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    user["id"] = str(user["_id"])
    return user


def create_tokens(user_id: str, role: str) -> dict:
    payload = {"sub": user_id, "role": role}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }


async def refresh_access_token(refresh_token: str) -> dict | None:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return None

    user_id = payload.get("sub")
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("is_active", True):
        return None

    return create_tokens(str(user["_id"]), user["role"])
