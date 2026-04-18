"""Seed an admin account if one does not already exist."""

import asyncio
from datetime import datetime, timezone

from api.core.config import get_settings
from api.core.database import connect_db, close_db, get_db
from api.core.security import hash_password

settings = get_settings()
ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD


async def seed_admin():
    await connect_db()
    db = get_db()

    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    if existing:
        print(f"Admin account '{ADMIN_EMAIL}' already exists — skipping.")
    else:
        await db.users.insert_one({
            "email": ADMIN_EMAIL,
            "hashed_password": hash_password(ADMIN_PASSWORD),
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "consent_camera": False,
            "created_at": datetime.now(timezone.utc),
        })
        print(f"Admin account '{ADMIN_EMAIL}' created successfully.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed_admin())
