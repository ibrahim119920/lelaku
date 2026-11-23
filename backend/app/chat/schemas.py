import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.chat.models import MESSAGE_MAX_LENGTH


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)


class MessageOut(BaseModel):
    message_id: uuid.UUID
    trip_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    content: str
    sent_at: datetime
