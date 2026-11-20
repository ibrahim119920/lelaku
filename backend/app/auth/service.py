from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository as repo
from app.auth.models import User
from app.auth.schemas import LoginRequest, ProfileUpdateRequest, RegisterRequest
from app.core.config import get_settings
from app.core.exceptions import ApiError
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)

_EMAIL_TAKEN = ApiError(
    409, "EMAIL_ALREADY_EXISTS", "Email sudah terdaftar. Gunakan email lain atau masuk."
)


def _email_taken() -> ApiError:
    return ApiError(_EMAIL_TAKEN.status_code, _EMAIL_TAKEN.code, _EMAIL_TAKEN.message)


async def register(session: AsyncSession, data: RegisterRequest) -> User:
    email = str(data.email).strip().lower()
    if await repo.email_exists(session, email):
        raise _email_taken()

    user = User(
        name=data.name,
        email=email,
        phone=data.phone,
        password_hash=await hash_password(data.password),
        identity_status="unverified",
    )
    repo.add_user(session, user)
    try:
        await session.commit()
    except IntegrityError as error:
        # Dua register bersamaan dengan email sama lolos pengecekan di atas;
        # unique index lower(email) yang menang.
        await session.rollback()
        if "uq_users_email_lower" in str(error.orig):
            raise _email_taken() from error
        raise
    await session.refresh(user)
    return user


async def login(session: AsyncSession, data: LoginRequest) -> tuple[User, str, datetime]:
    """Mengembalikan (user, token mentah untuk cookie, waktu kedaluwarsa)."""
    email = str(data.email).strip().lower()
    user = await repo.get_user_by_email(session, email)

    # Selalu jalankan satu verifikasi penuh (verify_password mengurus kasus user tidak ada),
    # dan beri respons yang sama untuk email tak terdaftar maupun password salah.
    if not await verify_password(data.password, user.password_hash if user else None) or user is None:
        raise ApiError(401, "AUTH_INVALID", "Email atau kata sandi salah.")

    token = generate_session_token()
    expires_at = datetime.now(UTC) + timedelta(seconds=get_settings().session_ttl_seconds)
    repo.add_session(session, token_hash=hash_session_token(token), user_id=user.user_id, expires_at=expires_at)
    await session.commit()
    await session.refresh(user)
    return user, token, expires_at


async def logout(session: AsyncSession, raw_token: str | None) -> None:
    """Idempotent: tanpa cookie atau dengan sesi yang sudah mati tetap sukses."""
    if not raw_token:
        return
    user_session = await repo.get_session(session, hash_session_token(raw_token))
    if user_session is not None and user_session.revoked_at is None:
        user_session.revoked_at = datetime.now(UTC)
        await session.commit()


async def update_profile(session: AsyncSession, user: User, data: ProfileUpdateRequest) -> User:
    user.name = data.name
    user.phone = data.phone
    await session.commit()
    await session.refresh(user)
    return user
