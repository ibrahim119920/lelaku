import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import User
from backend.app.chat.models import Message


async def list_messages(
    session: AsyncSession, trip_id: uuid.UUID, *, after: datetime | None, limit: int
) -> list[tuple[Message, str]]:
    """Tanpa `after`: `limit` pesan terbaru. Dengan `after`: pesan setelah waktu itu (untuk polling).

    Hasil selalu urut dari yang paling lama.
    """
    stmt = (
        select(Message, User.name)
        .join(User, User.user_id == Message.sender_id)
        .where(Message.trip_id == trip_id)
    )
    if after is not None:
        stmt = stmt.where(Message.sent_at > after).order_by(Message.sent_at).limit(limit)
        return [tuple(row) for row in await session.execute(stmt)]

    stmt = stmt.order_by(Message.sent_at.desc()).limit(limit)
    return [tuple(row) for row in reversed((await session.execute(stmt)).all())]


def add_message(session: AsyncSession, message: Message) -> None:
    session.add(message)
