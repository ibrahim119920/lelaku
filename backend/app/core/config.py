from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lelaku"
    db_disable_statement_cache: bool = False

    # Sesi server-side: cookie berisi token opaque, database hanya menyimpan hash SHA-256-nya.
    session_cookie_name: str = "lelaku_session"
    session_ttl_seconds: int = Field(default=7 * 24 * 60 * 60, ge=300, le=30 * 24 * 60 * 60)
    # Cookie `Secure` aktif untuk semua nilai selain "dev"/"development".
    app_env: str = "production"

    app_timezone: str = "Asia/Jakarta"
    cors_origins: str = "http://localhost:3000"

    @field_validator("database_url")
    @classmethod
    def use_asyncpg_driver(cls, value: str) -> str:
        # Connection string dari Supabase berbentuk "postgresql://..."; engine async butuh asyncpg.
        value = value.strip()
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                value = "postgresql+asyncpg://" + value[len(prefix) :]
                break

        # libpq memakai `sslmode=...`, tapi asyncpg lewat SQLAlchemy hanya mengenal `ssl=...`
        # (nilainya sama: require, verify-full, dst.). Tanpa ini koneksi gagal dengan
        # "connect() got an unexpected keyword argument 'sslmode'".
        url = make_url(value)
        if "sslmode" in url.query:
            query = dict(url.query)
            query.setdefault("ssl", query.pop("sslmode"))
            query.pop("sslmode", None)
            value = url.set(query=query).render_as_string(hide_password=False)
        return value

    @property
    def secure_cookie(self) -> bool:
        return self.app_env.strip().lower() not in {"dev", "development"}

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
