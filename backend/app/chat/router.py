import uuid

from fastapi import APIRouter, Query, status
from pydantic import AwareDatetime

from app.chat import service
from app.chat.schemas import MessageCreate, MessageOut
from app.core.deps import CurrentUserId, DbSession

messages_router = APIRouter(prefix="/trips/{trip_id}/messages", tags=["messages"])


@messages_router.get("", response_model=list[MessageOut])
async def list_messages(
    trip_id: uuid.UUID,
    session: DbSession,
    user_id: CurrentUserId,
    after: AwareDatetime | None = Query(None, description="Polling: isi dengan sent_at pesan terakhir yang sudah dimiliki"),
    limit: int = Query(50, ge=1, le=200),
):
    return await service.list_messages(session, user_id, trip_id, after=after, limit=limit)


@messages_router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(trip_id: uuid.UUID, data: MessageCreate, session: DbSession, user_id: CurrentUserId):
    return await service.send_message(session, user_id, trip_id, data)
