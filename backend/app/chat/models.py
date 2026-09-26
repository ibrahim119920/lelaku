import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.base import Base, UUIDText

MESSAGE_MAX_LENGTH = 2000


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_trip_id_sent_at", "trip_id", "sent_at"),)

    message_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trips.trip_id", ondelete="CASCADE"))
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(String(MESSAGE_MAX_LENGTH))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
