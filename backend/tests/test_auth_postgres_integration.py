"""Opt-in LL-05 lifecycle check against an explicitly allow-listed staging DB."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, inspect, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from backend.app.database import DatabaseConfigurationError, _get_postgres_url
from backend.app.dependencies import get_database_session
from backend.app.main import app
from backend.app.models import DriverProfile, User, UserSession


def _supabase_project_ref(url: URL) -> str | None:
    """Return the project ref encoded in a direct or shared-pooler Supabase URL."""
    host = (url.host or "").lower().rstrip(".")
    if host.endswith(".supabase.co"):
        labels = host.split(".")
        if len(labels) == 4 and labels[0] == "db":
            return labels[1]

    if host.endswith(".pooler.supabase.com"):
        username = url.username or ""
        if "." in username:
            return username.rsplit(".", 1)[1].lower()

    return None


def _allowlisted_test_url(raw_url: str, expected_project_ref: str) -> URL:
    """Require a separate URL and an exact Supabase staging project identity."""
    if not raw_url.strip() or not expected_project_ref.strip():
        raise ValueError("A dedicated test URL and project-ref allowlist are required.")

    try:
        url = _get_postgres_url(raw_url)
    except DatabaseConfigurationError:
        raise ValueError("The dedicated test URL is not a valid PostgreSQL URL.") from None

    actual_project_ref = _supabase_project_ref(url)
    if (
        url.drivername != "postgresql+psycopg"
        or actual_project_ref is None
        or actual_project_ref != expected_project_ref.strip().lower()
    ):
        raise ValueError("The URL does not match the allow-listed Supabase project.")

    return url


@pytest.mark.parametrize(
    ("connection_url", "expected_ref"),
    [
        ("postgresql://postgres:pw@db.stagingref.supabase.co:5432/postgres", "stagingref"),
        (
            "postgresql://postgres.stagingref:pw@aws-1-us-east-2.pooler.supabase.com:5432/postgres",
            "stagingref",
        ),
        ("postgresql://postgres:pw@db.productionref.supabase.co:5432/postgres", "productionref"),
        ("postgresql://postgres:pw@db.example.test:5432/postgres", None),
        (
            "postgresql://postgres:pw@aws-1-us-east-2.pooler.supabase.com:5432/postgres",
            None,
        ),
    ],
)
def test_supabase_project_ref_is_read_from_host_or_pooler_username(
    connection_url: str,
    expected_ref: str | None,
):
    from sqlalchemy.engine import make_url

    assert _supabase_project_ref(make_url(connection_url)) == expected_ref


@pytest.mark.parametrize(
    ("connection_url", "allowed_ref", "allowed"),
    [
        ("postgresql://postgres:pw@db.stagingref.supabase.co:5432/postgres", "stagingref", True),
        ("postgresql://postgres.prodref:pw@aws-1-us-east-2.pooler.supabase.com:5432/postgres", "stagingref", False),
        ("postgresql://postgres:pw@db.example.test:5432/postgres", "stagingref", False),
    ],
)
def test_test_database_requires_exact_project_reference_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    connection_url: str,
    allowed_ref: str,
    allowed: bool,
):
    monkeypatch.setenv("APP_ENV", "development")
    if allowed:
        assert _allowlisted_test_url(connection_url, allowed_ref).host
    else:
        with pytest.raises(ValueError, match="allow-listed"):
            _allowlisted_test_url(connection_url, allowed_ref)


def test_test_database_does_not_fall_back_to_general_database_url(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("APP_ENV", "development")

    with pytest.raises(ValueError, match="dedicated test URL"):
        _allowlisted_test_url("", "stagingref")


@pytest.mark.skipif(
    os.getenv("LL05_RUN_POSTGRES_INTEGRATION") != "1",
    reason="requires an explicit staging-only URL and Supabase project-ref allowlist",
)
def test_register_login_profile_session_and_logout_on_temporary_supabase(
    monkeypatch: pytest.MonkeyPatch,
):
    raw_test_url = os.getenv("LL05_TEST_DATABASE_URL", "").strip()
    allowed_project_ref = os.getenv("LL05_TEST_SUPABASE_PROJECT_REF", "").strip().lower()
    monkeypatch.setenv("APP_ENV", "development")
    try:
        database_url = _allowlisted_test_url(raw_test_url, allowed_project_ref)
    except ValueError:
        pytest.fail(
            "Target bukan URL Supabase staging yang secara eksplisit di-allowlist; tidak ada koneksi dibuat.",
            pytrace=False,
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
    created_user_ids: set[str] = set()
    previous_overrides = app.dependency_overrides.copy()

    def override_database_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        if engine.dialect.name != "postgresql":
            pytest.fail("Integration test membutuhkan PostgreSQL.", pytrace=False)

        required_tables = {"users", "driver_profiles", "user_sessions", "alembic_version"}
        with engine.connect() as connection:
            missing_tables = required_tables - set(
                inspect(connection).get_table_names(schema="public")
            )
        if missing_tables:
            pytest.fail(
                "Schema LL-05 belum lengkap; jalankan migrasi sebelum integration test.",
                pytrace=False,
            )

        emails = [
            f"ll05-{uuid4().hex}@example.com",
            f"ll05-{uuid4().hex}@example.com",
        ]
        with Session(engine) as session:
            collisions = session.scalars(
                select(User.user_id).where(User.email.in_(emails))
            ).all()
        if collisions:
            pytest.fail(
                "Email uji acak ternyata sudah digunakan; tidak ada baris yang diubah.",
                pytrace=False,
            )

        def remember_created_user(response, email: str) -> None:
            # A successful insert is recorded by primary key immediately. Cleanup
            # never selects by email, so a collision cannot delete an older row.
            if response.status_code != 201:
                return
            with Session(engine) as session:
                user_id = session.scalar(select(User.user_id).where(User.email == email))
            if user_id is not None:
                created_user_ids.add(str(user_id))

        first_session_token: str | None = None
        second_session_token: str | None = None
        with TestClient(app) as first_client, TestClient(app) as second_client:
            first_registration = first_client.post(
                "/auth/register",
                json={
                    "name": "LL05 Integration User A",
                    "email": emails[0],
                    "phone": "+628123456789",
                    "password": "integration-password-a",
                },
            )
            remember_created_user(first_registration, emails[0])
            assert first_registration.status_code == 201
            first_user_id = first_registration.json()["data"]["user_id"]
            assert first_registration.json()["data"]["identity_status"] == "unverified"
            assert "password_hash" not in first_registration.text

            duplicate = first_client.post(
                "/auth/register",
                json={
                    "name": "LL05 Duplicate",
                    "email": emails[0].upper(),
                    "phone": "+628123456789",
                    "password": "integration-password-a",
                },
            )
            assert duplicate.status_code == 409

            second_registration = second_client.post(
                "/auth/register",
                json={
                    "name": "LL05 Integration User B",
                    "email": emails[1],
                    "phone": "+628123456789",
                    "password": "integration-password-b",
                },
            )
            remember_created_user(second_registration, emails[1])
            assert second_registration.status_code == 201

            invalid_login = first_client.post(
                "/auth/login",
                json={"email": emails[0], "password": "incorrect-password"},
            )
            assert invalid_login.status_code == 401

            first_login = first_client.post(
                "/auth/login",
                json={"email": emails[0], "password": "integration-password-a"},
            )
            assert first_login.status_code == 200
            assert "password_hash" not in first_login.text
            first_session_token = first_login.cookies.get("lelaku_session")
            assert first_session_token

            second_login = second_client.post(
                "/auth/login",
                json={"email": emails[1], "password": "integration-password-b"},
            )
            assert second_login.status_code == 200
            second_session_token = second_login.cookies.get("lelaku_session")
            assert second_session_token

            assert first_client.get("/auth/me").json()["data"]["email"] == emails[0]
            assert first_client.get("/profile").json()["data"]["name"] == "LL05 Integration User A"
            assert second_client.get("/profile").json()["data"]["name"] == "LL05 Integration User B"

            forged_profile_update = second_client.patch(
                "/profile",
                json={
                    "name": "Must Not Be Applied",
                    "phone": "+628987654321",
                    "user_id": first_user_id,
                },
            )
            assert forged_profile_update.status_code == 422
            assert second_client.get("/profile").json()["data"]["name"] == "LL05 Integration User B"

            updated_profile = first_client.patch(
                "/profile",
                json={"name": "LL05 Profile Updated", "phone": "+628987654321"},
            )
            assert updated_profile.status_code == 200
            assert updated_profile.json()["data"]["name"] == "LL05 Profile Updated"
            assert updated_profile.json()["data"]["phone"] == "+628987654321"
            assert "password_hash" not in updated_profile.text
            assert second_client.get("/profile").json()["data"]["name"] == "LL05 Integration User B"

            logout = first_client.post("/auth/logout")
            assert logout.status_code == 204
            assert first_client.get("/auth/me").status_code == 401
            assert second_client.get("/auth/me").status_code == 200

            second_token_hash = sha256(second_session_token.encode("utf-8")).hexdigest()
            with Session(engine) as session:
                second_session = session.get(UserSession, second_token_hash)
                assert second_session is not None
                now = datetime.now(timezone.utc)
                second_session.created_at = now - timedelta(minutes=5)
                second_session.expires_at = now - timedelta(seconds=1)
                session.commit()

            assert second_client.get("/auth/me").status_code == 401
            assert second_client.get("/profile").status_code == 401

        with Session(engine) as session:
            first_user = session.get(User, first_user_id)
            second_user = session.scalar(select(User).where(User.email == emails[1]))
            assert first_user is not None and first_user.password_hash.startswith("$argon2id$")
            assert second_user is not None and second_user.password_hash.startswith("$argon2id$")
            assert first_user.name == "LL05 Profile Updated"
            assert first_user.identity_status == "unverified"

            first_sessions = session.scalars(
                select(UserSession).where(UserSession.user_id == first_user.user_id)
            ).all()
            second_sessions = session.scalars(
                select(UserSession).where(UserSession.user_id == second_user.user_id)
            ).all()
            assert len(first_sessions) == 1
            assert first_sessions[0].session_token_hash == sha256(
                first_session_token.encode("utf-8")
            ).hexdigest()
            assert first_sessions[0].revoked_at is not None
            assert len(second_sessions) == 1
            assert second_sessions[0].expires_at < datetime.now(timezone.utc)
            assert second_sessions[0].revoked_at is None
    finally:
        try:
            if created_user_ids:
                user_ids = list(created_user_ids)
                with Session(engine) as session:
                    session.execute(
                        delete(UserSession).where(UserSession.user_id.in_(user_ids))
                    )
                    session.execute(
                        delete(DriverProfile).where(DriverProfile.user_id.in_(user_ids))
                    )
                    session.execute(delete(User).where(User.user_id.in_(user_ids)))
                    session.commit()

                    assert not session.scalars(
                        select(User.user_id).where(User.user_id.in_(user_ids))
                    ).all()
                    assert not session.scalars(
                        select(UserSession.session_token_hash).where(
                            UserSession.user_id.in_(user_ids)
                        )
                    ).all()
                    assert not session.scalars(
                        select(DriverProfile.user_id).where(
                            DriverProfile.user_id.in_(user_ids)
                        )
                    ).all()
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            engine.dispose()
