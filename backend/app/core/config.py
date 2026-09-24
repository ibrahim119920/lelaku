from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lelaku"
    db_disable_statement_cache: bool = False

    jwt_secret: str = "change-me-in-development-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_cookie_name: str = "access_token"

    app_timezone: str = "Asia/Jakarta"
    cors_origins: str = "http://localhost:3000"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
