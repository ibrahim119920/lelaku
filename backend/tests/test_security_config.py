"""Test konfigurasi keamanan: cookie sesi, CORS, dan guard database test."""

import pytest

from app.auth import router as auth_router
from app.core.config import Settings
from tests.conftest import reject_unsafe_test_database_url

COOKIE = "lelaku_session"
VALID = {
    "name": "Naya Pengguna",
    "email": "naya@example.com",
    "phone": "+62 812-3456-789",
    "password": "rahasia-banget",
}


def test_cookie_is_secure_when_app_env_is_unset(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert Settings(_env_file=None).secure_cookie is True


@pytest.mark.parametrize("app_env", ["production", "staging", "Development!"])
def test_cookie_is_secure_outside_development(app_env):
    assert Settings(app_env=app_env, _env_file=None).secure_cookie is True


@pytest.mark.parametrize("app_env", ["dev", "development", " DEVELOPMENT "])
def test_cookie_is_not_secure_in_development(app_env):
    assert Settings(app_env=app_env, _env_file=None).secure_cookie is False


async def test_login_cookie_is_secure_in_production(client, monkeypatch):
    # Router memanggil get_settings() saat request; ganti dengan konfigurasi production.
    monkeypatch.setattr(
        auth_router, "get_settings", lambda: Settings(app_env="production", _env_file=None)
    )
    await client.post("/auth/register", json=VALID)
    resp = await client.post(
        "/auth/login", json={"email": VALID["email"], "password": VALID["password"]}
    )
    assert resp.status_code == 200
    assert "secure" in resp.headers["set-cookie"].lower()


async def test_cors_allows_configured_origin(client):
    resp = await client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert resp.headers["access-control-allow-credentials"] == "true"


async def test_cors_rejects_unknown_origin(client):
    resp = await client.options(
        "/auth/login",
        headers={
            "Origin": "https://jahat.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://user:secret@aws-0-ap-southeast-1.pooler.supabase.co:5432/postgres",
        "postgresql+asyncpg://db.ref123.supabase.co:5432/postgres",
        "postgresql://db.ref123.supabase.co/postgres",
        "postgres://db.ref123.supabase.co:5432/postgres",
    ],
)
def test_test_database_guard_rejects_supabase(url):
    with pytest.raises(RuntimeError, match="Supabase"):
        reject_unsafe_test_database_url(url)


def test_test_database_guard_checks_hostname_not_credentials():
    # Kata "supabase.co" di password tidak boleh memicu false positive.
    reject_unsafe_test_database_url(
        "postgresql+asyncpg://postgres:supabase.co@localhost:5432/lelaku_test"
    )


def test_test_database_guard_can_be_overridden_explicitly(monkeypatch):
    monkeypatch.setenv("ALLOW_SUPABASE_TEST_DB", "1")
    reject_unsafe_test_database_url(
        "postgresql+asyncpg://user:secret@aws-0-ap-southeast-1.pooler.supabase.co:5432/postgres"
    )


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://postgres:postgres@localhost:5432/lelaku_test",
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:55432/lelaku_test",
    ],
)
def test_test_database_guard_allows_local_database(url):
    reject_unsafe_test_database_url(url)
