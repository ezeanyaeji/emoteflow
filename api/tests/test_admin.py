"""Tests for /api/admin endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from tests.conftest import make_user, auth_header


@pytest.mark.asyncio
class TestAdminStats:
    async def test_stats_as_admin(self, client, _patch_db):
        uid, _ = make_user(_patch_db, role="admin", email="adm@test.com")
        fake_stats = {
            "period_hours": 24,
            "total_users": 1,
            "user_counts": {"admin": 1},
            "total_emotion_logs": 0,
            "active_students": 0,
            "emotion_distribution": {},
            "timeline": [],
            "recent_users": [],
        }
        with patch("services.dashboard.get_admin_stats", new_callable=AsyncMock, return_value=fake_stats):
            resp = await client.get("/api/admin/stats", headers=auth_header(uid, "admin"))
        assert resp.status_code == 200
        body = resp.json()
        assert "total_users" in body

    async def test_stats_as_student_forbidden(self, client, _patch_db):
        uid, _ = make_user(_patch_db, role="student", email="stu@test.com")
        resp = await client.get("/api/admin/stats", headers=auth_header(uid, "student"))
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestCreateTeacher:
    async def test_create_teacher(self, client, _patch_db):
        uid, _ = make_user(_patch_db, role="admin", email="adm2@test.com")
        resp = await client.post(
            "/api/admin/teachers",
            headers=auth_header(uid, "admin"),
            json={
                "email": "teacher@test.com",
                "password": "Teacher12",
                "first_name": "Teach",
                "last_name": "Er",
            },
        )
        assert resp.status_code == 201

    async def test_create_teacher_as_student(self, client, _patch_db):
        uid, _ = make_user(_patch_db, role="student", email="stu2@test.com")
        resp = await client.post(
            "/api/admin/teachers",
            headers=auth_header(uid, "student"),
            json={
                "email": "t2@test.com",
                "password": "Teacher12",
                "first_name": "Teach",
                "last_name": "Er",
            },
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestDeleteUser:
    async def test_delete_user(self, client, _patch_db):
        admin_id, _ = make_user(_patch_db, role="admin", email="adm3@test.com")
        stu_id, _ = make_user(_patch_db, role="student", email="del@test.com")
        resp = await client.delete(
            f"/api/admin/users/{stu_id}",
            headers=auth_header(admin_id, "admin"),
        )
        assert resp.status_code == 204

    async def test_delete_self_blocked(self, client, _patch_db):
        admin_id, _ = make_user(_patch_db, role="admin", email="adm4@test.com")
        resp = await client.delete(
            f"/api/admin/users/{admin_id}",
            headers=auth_header(admin_id, "admin"),
        )
        assert resp.status_code == 400
