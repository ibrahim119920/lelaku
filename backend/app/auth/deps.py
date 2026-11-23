"""Identitas user dari cookie sesi.

`get_current_user` adalah satu-satunya tempat sesi divalidasi. Modul trip/chat hanya
memakai `CurrentUserId` (lihat app/core/deps.py) yang dibangun di atasnya.
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository as repo
from app.auth.models import User
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ApiError
from app.core.security import hash_session_token


def _unauthenticated() -> ApiError:
    return ApiError(
        401,
        "AUTH_UNAUTHENTICATED",
        "Sesi tidak valid atau telah berakhir. Silakan masuk kembali.",
    )


async def get_current_user(request: Request, session: Annotated[AsyncSession, Depends(get_db)]) -> User:
    raw_token = request.cookies.get(get_settings().session_cookie_name)
    if not raw_token:
        raise _unauthenticated()

    user = await repo.get_active_user_by_token_hash(
        session, hash_session_token(raw_token), datetime.now(UTC)
    )
    if user is None:
        raise _unauthenticated()
    return user


async def get_current_user_id(user: Annotated[User, Depends(get_current_user)]) -> uuid.UUID:
    return user.user_id


CurrentUser = Annotated[User, Depends(get_current_user)]
