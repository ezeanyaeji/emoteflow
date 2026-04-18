"""Shared test fixtures — fake MongoDB, fake auth, and a test FastAPI client."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Fake in-memory MongoDB collections
# ---------------------------------------------------------------------------

class FakeCollection:
    """Minimal in-memory replacement for a Motor collection."""

    def __init__(self):
        self.docs = []
        self._next_id = 1

    async def insert_one(self, doc):
        from bson import ObjectId
        oid = ObjectId()
        doc["_id"] = oid
        self.docs.append(doc)
        result = MagicMock()
        result.inserted_id = oid
        return result

    async def find_one(self, query):
        for doc in self.docs:
            if self._matches(doc, query):
                return doc.copy()
        return None

    async def count_documents(self, query):
        return sum(1 for d in self.docs if self._matches(d, query))

    async def update_one(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                for key, val in update.get("$set", {}).items():
                    doc[key] = val
                return MagicMock(modified_count=1)
        return MagicMock(modified_count=0)

    async def delete_one(self, query):
        for i, doc in enumerate(self.docs):
            if self._matches(doc, query):
                self.docs.pop(i)
                return MagicMock(deleted_count=1)
        return MagicMock(deleted_count=0)

    def find(self, query=None):
        query = query or {}
        matched = [d.copy() for d in self.docs if self._matches(d, query)]
        return FakeCursor(matched)

    async def delete_many(self, query):
        to_remove = [i for i, d in enumerate(self.docs) if self._matches(d, query)]
        for i in reversed(to_remove):
            self.docs.pop(i)
        return MagicMock(deleted_count=len(to_remove))

    async def insert_many(self, docs):
        from bson import ObjectId
        ids = []
        for doc in docs:
            oid = ObjectId()
            doc["_id"] = oid
            self.docs.append(doc)
            ids.append(oid)
        result = MagicMock()
        result.inserted_ids = ids
        return result

    def aggregate(self, pipeline):
        """Very minimal aggregate — returns empty async iterator."""
        return FakeAggregateCursor([])

    async def create_index(self, *args, **kwargs):
        pass  # no-op for tests

    # ---- helpers ----------------------------------------------------------
    @staticmethod
    def _matches(doc, query):
        from bson import ObjectId
        for key, val in query.items():
            if key == "$or":
                if not any(FakeCollection._matches(doc, clause) for clause in val):
                    return False
                continue
            doc_val = doc.get(key)
            if isinstance(val, dict):
                for op, operand in val.items():
                    if op == "$gte" and not (doc_val is not None and doc_val >= operand):
                        return False
                    elif op == "$in" and doc_val not in operand:
                        return False
                    elif op == "$regex":
                        import re
                        flags = re.IGNORECASE if val.get("$options") == "i" else 0
                        if not re.search(operand, str(doc_val), flags):
                            return False
            elif doc_val != val:
                return False
        return True


class FakeAggregateCursor:
    """Async iterator for aggregate results."""
    def __init__(self, docs):
        self._docs = docs

    def __aiter__(self):
        self._iter = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs
        self._skip = 0
        self._limit = 0

    def sort(self, *args, **kwargs):
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __aiter__(self):
        sliced = self._docs[self._skip:]
        if self._limit:
            sliced = sliced[:self._limit]
        self._iter = iter(sliced)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

    async def to_list(self, length=None):
        sliced = self._docs[self._skip:]
        if self._limit:
            sliced = sliced[:self._limit]
        if length:
            sliced = sliced[:length]
        return sliced


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.emotions = FakeCollection()
        self.suggestions = FakeCollection()
        self.assignments = FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name, FakeCollection())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_db():
    return FakeDB()


@pytest.fixture()
def _patch_db(fake_db):
    """Set the module-level db variable so get_db() returns our fake."""
    import core.database as db_module
    original_db = db_module.db
    db_module.db = fake_db
    yield fake_db
    db_module.db = original_db


@pytest.fixture()
def _patch_model():
    """Patch the emotion model so it doesn't download from HF."""
    with patch("services.emotion.load_model"):
        yield


@pytest_asyncio.fixture()
async def client(_patch_db, _patch_model):
    """Async HTTPX test client that talks to the real FastAPI app."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- helpers to create users / tokens -----------------------------------

def make_user(fake_db, *, role="student", consent_camera=False, email="stu@test.com"):
    from bson import ObjectId
    from core.security import hash_password

    oid = ObjectId()
    user = {
        "_id": oid,
        "email": email,
        "hashed_password": hash_password("Test1234"),
        "first_name": "Test",
        "last_name": "User",
        "role": role,
        "consent_camera": consent_camera,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }
    fake_db.users.docs.append(user)
    return str(oid), user


def auth_header(user_id, role="student"):
    from core.security import create_access_token
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}
