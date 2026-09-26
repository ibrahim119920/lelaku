import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.chat import repository as repo
from backend.app.chat.models import Message
from backend.app.chat.schemas import MessageCreate, MessageOut
from backend.app.core.exceptions import ForbiddenError
from backend.app.trip import repository as trip_repo
from backend.app.trip import service as trip_service


async def _ensure_participant(session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID) -> None:
    trip = await trip_service.get_trip_or_404(session, trip_id)
    if not await trip_service.is_trip_participant(session, trip, user_id):
        raise ForbiddenError("Chat hanya untuk driver dan passenger yang sudah diterima di trip ini.")


async def list_messages(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, *, after: datetime | None, limit: int
) -> list[MessageOut]:
    await _ensure_participant(session, user_id, trip_id)
    return [
        MessageOut(
            message_id=message.message_id,
            trip_id=message.trip_id,
            sender_id=message.sender_id,
            sender_name=sender_name,
            content=message.content,
            sent_at=message.sent_at,
        )
        for message, sender_name in await repo.list_messages(session, trip_id, after=after, limit=limit)
    ]


async def send_message(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, data: MessageCreate
) -> MessageOut:
    await _ensure_participant(session, user_id, trip_id)
    message = Message(trip_id=trip_id, sender_id=user_id, content=data.content)
    repo.add_message(session, message)
    await session.commit()
    await session.refresh(message)
    sender = await trip_repo.get_user(session, user_id)
    return MessageOut(
        message_id=message.message_id,
        trip_id=message.trip_id,
        sender_id=message.sender_id,
        sender_name=sender.name,
        content=message.content,
        sent_at=message.sent_at,
    )
