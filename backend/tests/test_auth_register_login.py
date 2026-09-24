from datetime import datetime, timedelta, timezone
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.middleware.cors import CORSMiddleware

from backend.app.dependencies import get_database_session
from backend.app.main import app
from backend.app.models import Base, User, UserSession


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_database_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_database_session] = override_database_session
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("SESSION_TTL_SECONDS", raising=False)

    with TestClient(app) as client:
        yield client, engine

    app.dependency_overrides.clear()
    engine.dispose()


def register_user(client: TestClient, email: str = "naya@example.com"):
    return client.post(
        "/auth/register",
        json={
            "name": "Naya Pengguna",
            "email": email,
            "phone": "+628123456789",
            "password": "contoh-password-aman",
        },
    )


def login_user(client: TestClient, email: str = "naya@example.com"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": "contoh-password-aman"},
    )


def test_register_persists_only_argon2_hash_and_public_dto(api):
    client, engine = api

    response = register_user(client, "  NAYA@Example.com  ")

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["email"] == "naya@example.com"
    assert body["data"]["identity_status"] == "unverified"
    assert "password_hash" not in body["data"]
    assert "contoh-password-aman" not in response.text
    assert "set-cookie" not in response.headers

    with Session(engine) as session:
        user = session.scalar(select(User).where(User.email == "naya@example.com"))
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert user.password_hash != "contoh-password-aman"
        assert user.identity_status == "unverified"


def test_cookie_defaults_to_secure_when_app_environment_is_missing(
    api,
    monkeypatch: pytest.MonkeyPatch,
):
    client, _engine = api
    register_user(client)
    monkeypatch.delenv("APP_ENV", raising=False)

    response = login_user(client)

    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_register_rejects_case_insensitive_duplicate_email(api):
    client, _engine = api
    assert register_user(client).status_code == 201

    response = register_user(client, "NAYA@EXAMPLE.COM")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "EMAIL_ALREADY_EXISTS",
            "message": "Email sudah terdaftar. Gunakan email lain atau masuk.",
        }
    }


def test_login_creates_http_only_cookie_and_stores_only_token_digest(api):
    client, engine = api
    register_user(client)

    response = client.post(
        "/auth/login",
        json={"email": "NAYA@example.com", "password": "contoh-password-aman"},
    )

    assert response.status_code == 200
    assert "password_hash" not in response.text
    cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header
    assert "path=/" in cookie_header
    assert "secure" not in cookie_header
    raw_token = response.cookies.get("lelaku_session")
    assert raw_token

    with Session(engine) as session:
        stored_session = session.scalar(
            select(UserSession).where(UserSession.user_id == response.json()["data"]["user_id"])
        )
        assert stored_session is not None
        assert stored_session.session_token_hash == sha256(raw_token.encode()).hexdigest()
        assert stored_session.session_token_hash != raw_token
        assert stored_session.revoked_at is None


def test_invalid_credentials_have_identical_generic_response(api):
    client, _engine = api
    register_user(client)

    wrong_password = client.post(
        "/auth/login",
        json={"email": "naya@example.com", "password": "password-salah"},
    )
    missing_account = client.post(
        "/auth/login",
        json={"email": "lain@example.com", "password": "password-salah"},
    )

    assert wrong_password.status_code == missing_account.status_code == 401
    assert wrong_password.json() == missing_account.json()
    assert wrong_password.json()["error"]["code"] == "AUTH_INVALID"


def test_validation_error_uses_safe_contract_without_echoing_password(api):
    client, _engine = api

    response = client.post(
        "/auth/register",
        json={
            "name": "Naya",
            "email": "naya@example.com",
            "phone": "+628123456789",
            "password": "secret",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in response.json()["error"]["fields"]
    assert "secret" not in response.text


@pytest.mark.parametrize("app_env", ["production", "staging"])
def test_non_development_login_cookie_is_secure(
    api,
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
):
    client, _engine = api
    register_user(client)
    monkeypatch.setenv("APP_ENV", app_env)

    response = client.post(
        "/auth/login",
        json={"email": "naya@example.com", "password": "contoh-password-aman"},
    )

    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_cors_allows_only_configured_frontend_origin(api):
    client, _engine = api
    cors_options = next(
        middleware.kwargs
        for middleware in app.user_middleware
        if middleware.cls is CORSMiddleware
    )
    allowed_origin = cors_options["allow_origins"][0]

    allowed = client.options(
        "/auth/login",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    rejected = client.options(
        "/auth/login",
        headers={
            "Origin": "https://untrusted.invalid",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == allowed_origin
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-origin" not in rejected.headers


def test_current_user_and_profile_require_a_valid_session(api):
    client, _engine = api

    for response in (
        client.get("/auth/me"),
        client.get("/profile"),
        client.patch("/profile", json={"name": "Naya Baru", "phone": "+628123456789"}),
    ):
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_UNAUTHENTICATED"


def test_current_user_recognizes_a_valid_session_and_returns_safe_dto(api):
    client, _engine = api
    register_user(client)
    login_response = login_user(client)

    response = client.get("/auth/me")

    assert login_response.status_code == 200
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["data"]["email"] == "naya@example.com"
    assert response.json()["data"]["identity_status"] == "unverified"
    assert "password_hash" not in response.text


def test_expired_session_is_rejected(api):
    client, engine = api
    register_user(client)
    login_response = login_user(client)
    raw_token = login_response.cookies.get("lelaku_session")
    assert raw_token

    with Session(engine) as session:
        user_session = session.get(UserSession, sha256(raw_token.encode()).hexdigest())
        assert user_session is not None
        now = datetime.now(timezone.utc)
        user_session.created_at = now - timedelta(seconds=10)
        user_session.expires_at = now - timedelta(seconds=1)
        session.commit()

    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_UNAUTHENTICATED"


@pytest.mark.parametrize("app_env", ["development", "staging"])
def test_logout_revokes_server_session_and_clears_cookie(
    api,
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
):
    client, engine = api
    register_user(client)
    monkeypatch.setenv("APP_ENV", app_env)
    login_response = login_user(client)
    raw_token = login_response.cookies.get("lelaku_session")
    assert raw_token
    token_hash = sha256(raw_token.encode()).hexdigest()
    login_cookie = login_response.headers["set-cookie"].lower()

    logout_headers = (
        {"Cookie": f"lelaku_session={raw_token}"} if app_env == "staging" else None
    )
    response = client.post("/auth/logout", headers=logout_headers or {})

    assert response.status_code == 204
    assert response.content == b""
    assert response.headers["cache-control"] == "no-store"
    logout_cookie = response.headers["set-cookie"].lower()
    assert "max-age=0" in logout_cookie
    for attribute in ("httponly", "samesite=lax", "path=/"):
        assert attribute in login_cookie
        assert attribute in logout_cookie
    assert ("secure" in login_cookie) == ("secure" in logout_cookie)
    with Session(engine) as session:
        user_session = session.get(UserSession, token_hash)
        assert user_session is not None
        assert user_session.revoked_at is not None

    replayed_session = client.get(
        "/auth/me",
        headers={"Cookie": f"lelaku_session={raw_token}"},
    )
    assert replayed_session.status_code == 401


def test_logout_without_a_session_is_idempotent(api):
    client, _engine = api

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_profile_read_and_update_are_scoped_to_the_current_user(api):
    client, engine = api
    register_user(client)
    login_user(client)

    profile_response = client.get("/profile")
    assert profile_response.status_code == 200
    assert profile_response.headers["cache-control"] == "no-store"
    assert profile_response.json()["data"]["email"] == "naya@example.com"
    assert "password_hash" not in profile_response.text

    update_response = client.patch(
        "/profile",
        json={"name": "Naya Diperbarui", "phone": "+628987654321"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Naya Diperbarui"
    assert update_response.json()["data"]["phone"] == "+628987654321"
    assert update_response.json()["data"]["email"] == "naya@example.com"
    assert update_response.json()["data"]["identity_status"] == "unverified"
    assert "password_hash" not in update_response.text

    with Session(engine) as session:
        user = session.scalar(select(User).where(User.email == "naya@example.com"))
        assert user is not None
        assert user.name == "Naya Diperbarui"
        assert user.phone == "+628987654321"
        assert user.email == "naya@example.com"
        assert user.identity_status == "unverified"


@pytest.mark.parametrize("forbidden_field", ["email", "identity_status", "user_id"])
def test_profile_update_rejects_fields_outside_the_contract(api, forbidden_field: str):
    client, _engine = api
    register_user(client)
    login_user(client)
    payload = {"name": "Naya Baru", "phone": "+628123456789", forbidden_field: "other"}

    response = client.patch("/profile", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    profile_response = client.get("/profile")
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["name"] == "Naya Pengguna"


@pytest.mark.parametrize("phone", ["abcd", "123456"])
def test_profile_update_rejects_invalid_phone_numbers(api, phone: str):
    client, _engine = api
    register_user(client)
    login_user(client)

    response = client.patch(
        "/profile",
        json={"name": "Naya Baru", "phone": phone},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "phone" in response.json()["error"]["fields"]
    profile_response = client.get("/profile")
    assert profile_response.json()["data"]["phone"] == "+628123456789"


def test_registration_rejects_non_phone_text(api):
    client, _engine = api

    response = client.post(
        "/auth/register",
        json={
            "name": "Naya Pengguna",
            "email": "naya@example.com",
            "phone": "abcd",
            "password": "contoh-password-aman",
        },
    )

    assert response.status_code == 422
    assert "phone" in response.json()["error"]["fields"]


def test_profile_update_cannot_target_another_user(api):
    client, engine = api
    register_user(client, "first@example.com")
    login_user(client, "first@example.com")
    first_user_id = client.get("/auth/me").json()["data"]["user_id"]
    client.post("/auth/logout")

    register_user(client, "second@example.com")
    login_user(client, "second@example.com")
    response = client.patch(
        "/profile",
        json={
            "name": "Mencoba mengubah akun lain",
            "phone": "+628987654321",
            "user_id": first_user_id,
        },
    )

    assert response.status_code == 422
    with Session(engine) as session:
        first_user = session.get(User, first_user_id)
        assert first_user is not None
        assert first_user.name == "Naya Pengguna"
        assert first_user.phone == "+628123456789"
