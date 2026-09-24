from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.base import Base, UUIDText


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "identity_status IN ('verified', 'unverified')",
            name="ck_users_identity_status",
        ),
        CheckConstraint("total_ratings >= 0", name="ck_users_total_ratings_nonnegative"),
        CheckConstraint(
            "total_trips_completed >= 0",
            name="ck_users_total_trips_nonnegative",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    profile_photo: Mapped[str | None] = mapped_column(Text)
    identity_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="unverified"
    )
    avg_rating: Mapped[Decimal | None] = mapped_column(Numeric)
    total_ratings: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_trips_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )


Index("uq_users_email_lower", func.lower(User.email), unique=True)


class DriverProfile(Base):
    __tablename__ = "driver_profiles"
    __table_args__ = (
        CheckConstraint(
            "total_ratings_driver >= 0",
            name="ck_driver_profiles_total_ratings_nonnegative",
        ),
        CheckConstraint(
            "total_trips_as_driver >= 0",
            name="ck_driver_profiles_total_trips_nonnegative",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_url: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False)
    avg_rating_driver: Mapped[Decimal | None] = mapped_column(Numeric)
    total_ratings_driver: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    total_trips_as_driver: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        CheckConstraint(
            "expires_at > created_at",
            name="ck_user_sessions_expiry_after_creation",
        ),
        Index("ix_user_sessions_user_id_expires_at", "user_id", "expires_at"),
    )

    # Store only the SHA-256 digest of the opaque cookie value, never the raw token.
    session_token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    driver_id: Mapped[UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(32))
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    plate_number: Mapped[str] = mapped_column(String(32), unique=True)
    capacity: Mapped[int] = mapped_column(Integer)


# Import domain models so all tables share one metadata collection for Alembic.
from backend.app.chat.models import Message as Message  # noqa: E402, F401
from backend.app.trip.models import (  # noqa: E402, F401
    Rating as Rating,
    RideRequest as RideRequest,
    Trip as Trip,
    TripMatch as TripMatch,
    TripMember as TripMember,
)
