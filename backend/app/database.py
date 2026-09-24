from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
# Prefer service-local configuration while keeping the old root .env as a
# backwards-compatible fallback during the repository layout transition.
load_dotenv(BACKEND_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")


class DatabaseConfigurationError(RuntimeError):
    """Raised when the PostgreSQL connection string is missing or invalid."""


def _get_postgres_url(raw_url: str | None = None) -> URL:
    raw_url = (raw_url if raw_url is not None else os.getenv("DATABASE_URL", "")).strip()
    if not raw_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL belum dikonfigurasi di environment backend."
        )

    try:
        url = make_url(raw_url)
    except ArgumentError as error:
        raise DatabaseConfigurationError(
            "DATABASE_URL tidak valid. Gunakan connection string PostgreSQL."
        ) from error

    if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise DatabaseConfigurationError(
            "DATABASE_URL harus menggunakan PostgreSQL."
        )

    if not url.host or not url.database:
        raise DatabaseConfigurationError(
            "DATABASE_URL harus mencantumkan hostname dan nama database."
        )

    query = dict(url.query)
    app_env = os.getenv("APP_ENV", "production").strip().lower()
    is_development = app_env in {"dev", "development"}
    sslmode = str(query.get("sslmode", "")).strip().lower()
    if not sslmode:
        sslmode = "require" if is_development else "verify-full"

    if not is_development and sslmode != "verify-full":
        raise DatabaseConfigurationError(
            "Environment staging/production mewajibkan sslmode=verify-full."
        )

    local_hosts = {"localhost", "127.0.0.1", "::1"}
    host = url.host.strip("[]").lower()
    if sslmode in {"disable", "allow", "prefer"} and not (
        is_development and host in local_hosts
    ):
        raise DatabaseConfigurationError(
            "Mode TLS yang dapat menurunkan keamanan hanya boleh untuk PostgreSQL lokal development."
        )

    query["sslmode"] = sslmode

    return url.set(drivername="postgresql+psycopg", query=query)


@lru_cache(maxsize=1)
def get_database_engine() -> Engine:
    """Create one reusable SQLAlchemy pool for any PostgreSQL provider."""
    return create_engine(
        _get_postgres_url(),
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=2,
        pool_recycle=1800,
        connect_args={"connect_timeout": 10},
    )


def check_database_connection() -> None:
    """Run a lightweight query to confirm the configured database is reachable."""
    with get_database_engine().connect() as connection:
        result = connection.scalar(text("SELECT 1"))
        if result != 1:
            raise RuntimeError("Database health query returned an unexpected result.")
