import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserSession


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(func.lower(User.email) == email.lower()))


async def email_exists(session: AsyncSession, email: str) -> bool:
    return (
        await session.scalar(select(User.user_id).where(func.lower(User.email) == email.lower()))
    ) is not None


def add_user(session: AsyncSession, user: User) -> None:
    session.add(user)


def add_session(
    session: AsyncSession, *, token_hash: str, user_id: uuid.UUID, expires_at: datetime
) -> None:
    session.add(UserSession(session_token_hash=token_hash, user_id=user_id, expires_at=expires_at))


async def get_active_user_by_token_hash(
    session: AsyncSession, token_hash: str, now: datetime
) -> User | None:
    """User pemilik sesi yang belum dicabut dan belum kedaluwarsa, dalam satu query."""
    return await session.scalar(
        select(User)
        .join(UserSession, UserSession.user_id == User.user_id)
        .where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )


async def get_session(session: AsyncSession, token_hash: str) -> UserSession | None:
    return await session.get(UserSession, token_hash)
