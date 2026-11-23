from fastapi import APIRouter, Request, Response, status

from app.auth import service
from app.auth.deps import CurrentUser
from app.auth.schemas import (
    LoginRequest,
    ProfileUpdateRequest,
    PublicUser,
    RegisterRequest,
    UserDataEnvelope,
)
from app.core.config import get_settings
from app.core.deps import DbSession

auth_router = APIRouter(prefix="/auth", tags=["auth"])
profile_router = APIRouter(prefix="/profile", tags=["profile"])


def _no_store(response: Response) -> None:
    # Response berisi data akun/sesi; jangan biarkan di-cache browser atau proxy.
    response.headers["Cache-Control"] = "no-store"


def _envelope(user) -> UserDataEnvelope:
    return UserDataEnvelope(data=PublicUser.model_validate(user))


@auth_router.post("/register", response_model=UserDataEnvelope, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, response: Response, session: DbSession):
    _no_store(response)
    return _envelope(await service.register(session, data))


@auth_router.post("/login", response_model=UserDataEnvelope)
async def login(data: LoginRequest, response: Response, session: DbSession):
    _no_store(response)
    user, token, _expires_at = await service.login(session, data)
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        path="/",
    )
    return _envelope(user)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, session: DbSession) -> Response:
    settings = get_settings()
    await service.logout(session, request.cookies.get(settings.session_cookie_name))
    response = Response(status_code=status.HTTP_204_NO_CONTENT, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
    )
    return response


@auth_router.get("/me", response_model=UserDataEnvelope)
async def me(user: CurrentUser, response: Response):
    _no_store(response)
    return _envelope(user)


@profile_router.get("", response_model=UserDataEnvelope)
async def get_profile(user: CurrentUser, response: Response):
    _no_store(response)
    return _envelope(user)


@profile_router.patch("", response_model=UserDataEnvelope)
async def update_profile(
    data: ProfileUpdateRequest, user: CurrentUser, response: Response, session: DbSession
):
    _no_store(response)
    return _envelope(await service.update_profile(session, user, data))
