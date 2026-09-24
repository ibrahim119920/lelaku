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


def test_production_login_cookie_is_secure(api, monkeypatch: pytest.MonkeyPatch):
    client, _engine = api
    register_user(client)
    monkeypatch.setenv("APP_ENV", "production")

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
