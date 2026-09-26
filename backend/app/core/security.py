from typing import Annotated
from uuid import UUID

from fastapi import Depends

from backend.app.auth_dependencies import get_current_user_async
from backend.app.models import User


async def get_current_user_id(
    user: Annotated[User, Depends(get_current_user_async)],
) -> UUID:
    """Return the identity validated by LL-05's revocable database session."""
    return UUID(user.user_id)
