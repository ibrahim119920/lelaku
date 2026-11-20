"""Test auth & profile (LL-05): register, login, logout, sesi, dan batas keamanannya."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text

from app.auth.models import User, UserSession
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_session_token
from tests.conftest import auth, make_user

COOKIE = get_settings().session_cookie_name
VALID = {
    "name": "Naya Pengguna",
    "email": "Naya@Example.com",
    "phone": "+62 812-3456-789",
    "password": "rahasia-banget",
}


async def register(client, **overrides):
    return await client.post("/auth/register", json={**VALID, **overrides})


async def login(client, email="naya@example.com", password=VALID["password"]):
    return await client.post("/auth/login", json={"email": email, "password": password})


# ---------- register ----------


async def test_register_returns_public_user_without_secrets(client):
    resp = await register(client)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["email"] == "naya@example.com"  # dinormalisasi ke huruf kecil
    assert data["identity_status"] == "unverified"
    assert data["total_ratings"] == 0
    assert "password" not in data and "password_hash" not in data
    assert resp.headers["cache-control"] == "no-store"


async def test_register_stores_argon2_hash_not_plain_password(client):
    await register(client)
    async with SessionLocal() as session:
        user = await session.scalar(select(User))
    assert user.password_hash.startswith("$argon2")
    assert VALID["password"] not in user.password_hash


async def test_register_duplicate_email_is_case_insensitive(client):
    assert (await register(client)).status_code == 201
    resp = await register(client, email="NAYA@example.COM")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


async def test_register_validation_returns_field_errors(client):
    resp = await client.post(
        "/auth/register", json={"name": "N", "email": "bukan-email", "phone": "abc", "password": "pendek"}
    )
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["fields"]) == {"name", "email", "phone", "password"}


async def test_register_rejects_unknown_fields(client):
    resp = await register(client, identity_status="verified")
    assert resp.status_code == 422  # tidak boleh mengangkat diri sendiri jadi verified


# ---------- login / sesi ----------


async def test_login_sets_httponly_cookie_and_stores_only_hash(client):
    await register(client)
    resp = await login(client)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "naya@example.com"

    set_cookie = resp.headers["set-cookie"].lower()
    assert f"{COOKIE}=" in set_cookie
    assert "httponly" in set_cookie and "samesite=lax" in set_cookie and "path=/" in set_cookie

    raw_token = resp.cookies[COOKIE]
    async with SessionLocal() as session:
        stored = (await session.scalars(select(UserSession))).all()
    assert len(stored) == 1
    assert stored[0].session_token_hash == hash_session_token(raw_token)
    assert stored[0].session_token_hash != raw_token  # token mentah tidak disimpan


async def test_login_wrong_password_and_unknown_email_look_identical(client):
    await register(client)
    wrong_password = await login(client, password="salah-total")
    unknown_email = await login(client, email="tidakada@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["error"]["code"] == "AUTH_INVALID"
    assert COOKIE not in wrong_password.cookies


async def test_me_requires_valid_session(client):
    no_cookie = await client.get("/auth/me")
    assert no_cookie.status_code == 401
    assert no_cookie.json()["error"]["code"] == "AUTH_UNAUTHENTICATED"

    await register(client)
    await login(client)  # cookie tersimpan di client
    me = await client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "naya@example.com"


async def test_session_cookie_authenticates_trip_endpoints_too(client):
    await register(client)
    await login(client)
    assert (await client.get("/trips")).status_code == 200  # CurrentUserId lewat sesi yang sama


async def test_expired_session_is_rejected(client):
    user_id = await make_user()
    async with SessionLocal() as session:
        await session.execute(
            text("UPDATE user_sessions SET expires_at = :past, created_at = :earlier"),
            {"past": datetime.now(UTC) - timedelta(minutes=1), "earlier": datetime.now(UTC) - timedelta(hours=2)},
        )
        await session.commit()
    assert (await client.get("/auth/me", headers=auth(user_id))).status_code == 401


async def test_logout_revokes_session_server_side(client):
    await register(client)
    resp = await login(client)
    raw_token = resp.cookies[COOKIE]

    out = await client.post("/auth/logout")
    assert out.status_code == 204

    # Walau token yang sama dikirim ulang manual, sesi sudah dicabut di database.
    replay = await client.get("/auth/me", headers={"Cookie": f"{COOKIE}={raw_token}"})
    assert replay.status_code == 401
    async with SessionLocal() as session:
        stored = await session.scalar(select(UserSession))
    assert stored.revoked_at is not None


async def test_logout_is_idempotent_without_session(client):
    assert (await client.post("/auth/logout")).status_code == 204


async def test_each_login_creates_independent_session(client):
    await register(client)
    first = (await login(client)).cookies[COOKIE]
    second = (await login(client)).cookies[COOKIE]
    assert first != second  # token baru per login, bukan dipakai ulang


# ---------- profile ----------


async def test_profile_get_and_patch(client):
    await register(client)
    await login(client)

    assert (await client.get("/profile")).json()["data"]["name"] == "Naya Pengguna"

    resp = await client.patch("/profile", json={"name": "Naya Baru", "phone": "081234567890"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Naya Baru"
    assert (await client.get("/auth/me")).json()["data"]["phone"] == "081234567890"


@pytest.mark.parametrize("field", ["email", "identity_status", "avg_rating", "password_hash", "user_id"])
async def test_profile_patch_cannot_change_protected_fields(client, field):
    await register(client)
    await login(client)
    resp = await client.patch("/profile", json={"name": "Naya Baru", "phone": "081234567890", field: "x"})
    assert resp.status_code == 422


async def test_profile_requires_login(client):
    assert (await client.get("/profile")).status_code == 401
    assert (await client.patch("/profile", json={"name": "Aa", "phone": "081234567890"})).status_code == 401


async def test_users_are_isolated_by_session(client):
    first = await make_user("Pertama")
    second = await make_user("Kedua")
    one = await client.get("/auth/me", headers=auth(first))
    two = await client.get("/auth/me", headers=auth(second))
    assert one.json()["data"]["name"] == "Pertama"
    assert two.json()["data"]["name"] == "Kedua"
