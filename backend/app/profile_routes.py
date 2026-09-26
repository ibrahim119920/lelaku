from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.app.auth_dependencies import get_current_user
from backend.app.dependencies import get_database_session
from backend.app.models import User
from backend.app.schemas import ProfileUpdateRequest, UserDataEnvelope


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserDataEnvelope)
def get_profile(
    response: Response,
    user: User = Depends(get_current_user),
) -> UserDataEnvelope:
    response.headers["Cache-Control"] = "no-store"
    return UserDataEnvelope(data=user)


@router.patch("", response_model=UserDataEnvelope)
def update_profile(
    payload: ProfileUpdateRequest,
    response: Response,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_database_session),
) -> UserDataEnvelope:
    response.headers["Cache-Control"] = "no-store"
    user.name = payload.name
    user.phone = payload.phone
    session.commit()
    session.refresh(user)
    return UserDataEnvelope(data=user)
