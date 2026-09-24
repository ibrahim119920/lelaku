"""Model tabel milik modul auth & identity.

TODO(auth): PLACEHOLDER. Modul auth dikerjakan anggota tim lain dan belum masuk
repo. Model ini dibuat sesuai ERD hanya supaya modul trip/chat punya foreign key
dan bisa dites. Saat kode auth asli masuk, hapus file ini beserta migration
`0001_auth_placeholder`, lalu arahkan `down_revision` migration trip ke revision
terakhir milik modul auth.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    profile_photo: Mapped[str | None] = mapped_column(String(512))
    avg_rating: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_trips_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    document_url: Mapped[str | None] = mapped_column(String(512))
    verification_status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending"
    )
    avg_rating_driver: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    total_ratings_driver: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_trips_as_driver: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(32))
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    plate_number: Mapped[str] = mapped_column(String(32), unique=True)
    capacity: Mapped[int] = mapped_column(Integer)


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    session_token_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
