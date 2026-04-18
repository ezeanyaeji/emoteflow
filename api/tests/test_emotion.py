"""Tests for /api/emotion endpoints."""

import io
import pytest
from unittest.mock import patch
from tests.conftest import make_user, auth_header
from models.emotion import EmotionScores


FAKE_PREDICTION = {
    "emotion": "Happy",
    "confidence": 0.92,
    "scores": EmotionScores(
        Angry=0.01, Disgust=0.0, Fear=0.02,
        Happy=0.92, Neutral=0.03, Sad=0.01, Surprise=0.01,
    ),
}


@pytest.mark.asyncio
class TestPredict:
    async def test_predict_success(self, client, _patch_db):
        uid, _ = make_user(_patch_db, email="pred@test.com", consent_camera=True)
        with patch("routers.emotion.predict_emotion", return_value=FAKE_PREDICTION):
            resp = await client.post(
                "/api/emotion/predict",
                headers=auth_header(uid),
                files={"file": ("face.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["emotion"] == "Happy"
        assert body["confidence"] == 0.92
        assert body["suggestion"] is not None

    async def test_predict_no_consent(self, client, _patch_db):
        uid, _ = make_user(_patch_db, email="nocam@test.com", consent_camera=False)
        resp = await client.post(
            "/api/emotion/predict",
            headers=auth_header(uid),
            files={"file": ("face.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
        )
        assert resp.status_code == 403
        assert "consent" in resp.json()["detail"].lower()

    async def test_predict_non_image(self, client, _patch_db):
        uid, _ = make_user(_patch_db, email="txt@test.com", consent_camera=True)
        resp = await client.post(
            "/api/emotion/predict",
            headers=auth_header(uid),
            files={"file": ("doc.txt", b"hello world", "text/plain")},
        )
        assert resp.status_code == 400

    async def test_predict_unauthenticated(self, client):
        resp = await client.post(
            "/api/emotion/predict",
            files={"file": ("face.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestHistory:
    async def test_history_empty(self, client, _patch_db):
        uid, _ = make_user(_patch_db, email="hist@test.com")
        resp = await client.get("/api/emotion/history", headers=auth_header(uid))
        assert resp.status_code == 200
        body = resp.json()
        assert body["logs"] == []
        assert body["total"] == 0

    async def test_history_with_data(self, client, _patch_db):
        uid, _ = make_user(_patch_db, email="hist2@test.com", consent_camera=True)
        # Insert an emotion log directly
        from datetime import datetime, timezone
        _patch_db.emotions.docs.append({
            "_id": __import__("bson").ObjectId(),
            "user_id": uid,
            "session_id": "sess-1",
            "emotion": "Happy",
            "confidence": 0.9,
            "scores": {"Angry": 0, "Disgust": 0, "Fear": 0, "Happy": 0.9,
                        "Neutral": 0.05, "Sad": 0.03, "Surprise": 0.02},
            "timestamp": datetime.now(timezone.utc),
        })
        resp = await client.get("/api/emotion/history", headers=auth_header(uid))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["logs"][0]["emotion"] == "Happy"
