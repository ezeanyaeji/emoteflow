"""Tests for /api/auth endpoints."""

import pytest
from tests.conftest import make_user, auth_header


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client, _patch_db):
        resp = await client.post("/api/auth/register", json={
            "email": "new@test.com",
            "password": "StrongPass1",
            "first_name": "Jane",
            "last_name": "Doe",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "new@test.com"
        assert body["role"] == "student"

    async def test_register_duplicate_email(self, client, _patch_db):
        make_user(_patch_db, email="dup@test.com")
        resp = await client.post("/api/auth/register", json={
            "email": "dup@test.com",
            "password": "StrongPass1",
            "first_name": "Jane",
            "last_name": "Doe",
        })
        # Email taken → 409
        assert resp.status_code == 409

    async def test_register_short_password(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "x@test.com",
            "password": "short",
            "first_name": "Jane",
            "last_name": "Doe",
        })
        assert resp.status_code == 422  # validation error


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client, _patch_db):
        make_user(_patch_db, email="login@test.com")
        resp = await client.post("/api/auth/login", json={
            "email": "login@test.com",
            "password": "Test1234",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client, _patch_db):
        make_user(_patch_db, email="login2@test.com")
        resp = await client.post("/api/auth/login", json={
            "email": "login2@test.com",
            "password": "WrongPass9",
        })
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@test.com",
            "password": "Whatever1",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestMe:
    async def test_me_authenticated(self, client, _patch_db):
        uid, _ = make_user(_patch_db, email="me@test.com")
        resp = await client.get("/api/auth/me", headers=auth_header(uid))
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@test.com"

    async def test_me_no_token(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    async def test_logout(self, client):
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Logged out"
