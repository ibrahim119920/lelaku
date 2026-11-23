"""Model tabel milik modul auth & identity (LL-05), memakai UUID dan SQLAlchemy async.

Diporting dari branch develop (versi sync, `user_id` Text) ke gaya backend ini: kolom
`user_id` bertipe UUID supaya foreign key dari trip/chat cocok. Perubahan dari versi
placeholder ada di migration `0006_auth_identity`.

`Vehicle` belum punya modul sendiri (develop tidak menyertakannya). Ia tetap di sini
karena `trips.vehicle_id` bergantung padanya; belum ada endpoint untuk mengelolanya.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Nama pendek: NAMING_CONVENTION menambahkan prefix "ck_users_".
        CheckConstraint("identity_status IN ('verified', 'unverified')", name="identity_status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    profile_photo: Mapped[str | None] = mapped_column(String(512))
    # Status verifikasi identitas akun (FR-03). Berbeda dari DriverProfile.verification_status.
    identity_status: Mapped[str] = mapped_column(
        String(16), default="unverified", server_default="unverified"
    )
    avg_rating: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_trips_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


# Email unik tanpa membedakan huruf besar/kecil; ini penjaga sebenarnya dari register ganda.
Index("uq_users_email_lower", func.lower(User.email), unique=True)


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
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="expiry_after_creation"),
        Index("ix_user_sessions_user_id_expires_at", "user_id", "expires_at"),
    )

    # Hanya digest SHA-256 dari token cookie yang disimpan, tidak pernah token mentahnya.
    session_token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.user_id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
