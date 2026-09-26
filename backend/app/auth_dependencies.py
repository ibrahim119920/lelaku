from datetime import datetime, timezone
from hashlib import sha256

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.dependencies import get_database_session
from backend.app.errors import ApiError
from backend.app.models import User, UserSession


SESSION_COOKIE_NAME = "lelaku_session"


def get_current_user(
    request: Request,
    session: Session = Depends(get_database_session),
) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw_token:
        raise ApiError(
            status_code=401,
            code="AUTH_UNAUTHENTICATED",
            message="Sesi tidak valid atau telah berakhir. Silakan masuk kembali.",
        )

    token_hash = sha256(raw_token.encode("utf-8")).hexdigest()
    user = session.scalar(
        select(User)
        .join(UserSession, UserSession.user_id == User.user_id)
        .where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    if user is None:
        raise ApiError(
            status_code=401,
            code="AUTH_UNAUTHENTICATED",
            message="Sesi tidak valid atau telah berakhir. Silakan masuk kembali.",
        )

    return user


async def get_current_user_async(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    """Validate the same opaque session through the async API database session."""
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw_token:
        raise ApiError(
            status_code=401,
            code="AUTH_UNAUTHENTICATED",
            message="Sesi tidak valid atau telah berakhir. Silakan masuk kembali.",
        )

    token_hash = sha256(raw_token.encode("utf-8")).hexdigest()
    user = await session.scalar(
        select(User)
        .join(UserSession, UserSession.user_id == User.user_id)
        .where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    if user is None:
        raise ApiError(
            status_code=401,
            code="AUTH_UNAUTHENTICATED",
            message="Sesi tidak valid atau telah berakhir. Silakan masuk kembali.",
        )

    return user
