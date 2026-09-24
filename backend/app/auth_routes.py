from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
import secrets

from fastapi import APIRouter, Depends, Response
from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.dependencies import get_database_session
from backend.app.errors import ApiError
from backend.app.models import User, UserSession
from backend.app.schemas import LoginRequest, RegisterRequest, UserDataEnvelope


router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_COOKIE_NAME = "lelaku_session"
DEFAULT_SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
MAX_SESSION_TTL_SECONDS = 30 * 24 * 60 * 60

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(32))


def _session_ttl_seconds() -> int:
    raw_ttl = os.getenv("SESSION_TTL_SECONDS", str(DEFAULT_SESSION_TTL_SECONDS))
    try:
        ttl = int(raw_ttl)
    except ValueError as error:
        raise RuntimeError("SESSION_TTL_SECONDS harus berupa bilangan bulat.") from error

    if not 300 <= ttl <= MAX_SESSION_TTL_SECONDS:
        raise RuntimeError("SESSION_TTL_SECONDS harus antara 300 dan 2592000.")
    return ttl


def _secure_cookie() -> bool:
    return os.getenv("APP_ENV", "development").strip().lower() in {
        "prod",
        "production",
    }


def _is_email_unique_violation(error: IntegrityError) -> bool:
    diagnostic = getattr(error.orig, "diag", None)
    if getattr(diagnostic, "constraint_name", None) == "uq_users_email_lower":
        return True
    return "uq_users_email_lower" in str(error.orig)


@router.post(
    "/register",
    status_code=201,
    response_model=UserDataEnvelope,
)
def register(
    payload: RegisterRequest,
    response: Response,
    session: Session = Depends(get_database_session),
) -> UserDataEnvelope:
    response.headers["Cache-Control"] = "no-store"
    email = str(payload.email).strip().lower()

    existing_user_id = session.scalar(
        select(User.user_id).where(func.lower(User.email) == email)
    )
    if existing_user_id is not None:
        raise ApiError(
            status_code=409,
            code="EMAIL_ALREADY_EXISTS",
            message="Email sudah terdaftar. Gunakan email lain atau masuk.",
        )

    user = User(
        name=payload.name,
        email=email,
        phone=payload.phone,
        password_hash=password_hasher.hash(payload.password),
        identity_status="unverified",
    )
    session.add(user)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _is_email_unique_violation(error):
            raise ApiError(
                status_code=409,
                code="EMAIL_ALREADY_EXISTS",
                message="Email sudah terdaftar. Gunakan email lain atau masuk.",
            ) from error
        raise

    session.refresh(user)
    return UserDataEnvelope(data=user)


@router.post("/login", response_model=UserDataEnvelope)
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_database_session),
) -> UserDataEnvelope:
    response.headers["Cache-Control"] = "no-store"
    email = str(payload.email).strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == email))

    stored_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    try:
        password_matches = password_hasher.verify(payload.password, stored_hash)
    except Exception:
        # Fail closed for malformed/unsupported stored hashes without revealing
        # which part of the credentials was invalid.
        password_matches = False

    if user is None or not password_matches:
        raise ApiError(
            status_code=401,
            code="AUTH_INVALID",
            message="Email atau kata sandi salah.",
        )

    ttl_seconds = _session_ttl_seconds()
    raw_session_token = secrets.token_urlsafe(32)
    session_token_hash = sha256(raw_session_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    session.add(
        UserSession(
            session_token_hash=session_token_hash,
            user_id=user.user_id,
            expires_at=expires_at,
        )
    )
    session.commit()
    session.refresh(user)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_session_token,
        max_age=ttl_seconds,
        httponly=True,
        secure=_secure_cookie(),
        samesite="lax",
        path="/",
    )
    return UserDataEnvelope(data=user)
