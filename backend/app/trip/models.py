import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.base import Base, UUIDText


class TripStatus(str, enum.Enum):
    published = "published"
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("available_seats >= 0", name="available_seats_non_negative"),
        CheckConstraint("cost_per_seat >= 0", name="cost_per_seat_non_negative"),
        CheckConstraint("origin_lat BETWEEN -90 AND 90", name="origin_lat_range"),
        CheckConstraint("origin_lng BETWEEN -180 AND 180", name="origin_lng_range"),
        CheckConstraint("destination_lat BETWEEN -90 AND 90", name="destination_lat_range"),
        CheckConstraint("destination_lng BETWEEN -180 AND 180", name="destination_lng_range"),
        Index("ix_trips_status_departure_time", "status", "departure_time"),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("vehicles.vehicle_id", ondelete="RESTRICT")
    )
    origin_lat: Mapped[float] = mapped_column(Float)
    origin_lng: Mapped[float] = mapped_column(Float)
    destination_lat: Mapped[float] = mapped_column(Float)
    destination_lng: Mapped[float] = mapped_column(Float)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    available_seats: Mapped[int] = mapped_column(Integer)
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_status"),
        default=TripStatus.published,
        server_default=TripStatus.published.value,
    )
    estimated_total_cost: Mapped[float] = mapped_column(Float)
    cost_per_seat: Mapped[float] = mapped_column(Float)


class TripMatch(Base):
    """Ada di ERD tapi sengaja tidak diisi: /trips/recommended dihitung on-the-fly.

    Dipertahankan untuk kemungkinan precompute di masa depan. Jangan tambahkan
    repository/service yang insert/upsert ke tabel ini tanpa keputusan tim.
    """

    __tablename__ = "trip_matches"

    match_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.trip_id", ondelete="CASCADE"), index=True
    )
    matched_trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.trip_id", ondelete="CASCADE")
    )
    route_similarity: Mapped[float] = mapped_column(Float)
    match_score: Mapped[float] = mapped_column(Float)


class RideRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class RideRequest(Base):
    __tablename__ = "ride_requests"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'accepted', 'rejected')", name="status_valid"),
        # Satu request aktif (pending/accepted) per passenger per trip; boleh request ulang setelah rejected.
        Index(
            "uq_ride_requests_active_per_requester",
            "trip_id",
            "requester_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'accepted')"),
        ),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("trips.trip_id", ondelete="CASCADE"), index=True
    )
    pickup: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(16), default=RideRequestStatus.pending.value, server_default=RideRequestStatus.pending.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TripMemberStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"


class TripMember(Base):
    """Passenger yang request-nya di-accept. Driver TIDAK dicatat di sini (anggota implisit via trips.driver_id)."""

    __tablename__ = "trip_members"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'cancelled')", name="status_valid"),
        UniqueConstraint("trip_id", "user_id", name="uq_trip_members_trip_id_user_id"),
    )

    trip_member_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trips.trip_id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    ride_request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ride_requests.request_id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[str] = mapped_column(
        String(16), default=TripMemberStatus.active.value, server_default=TripMemberStatus.active.value
    )


class RatingRoleContext(str, enum.Enum):
    driver_to_passenger = "driver_to_passenger"
    passenger_to_driver = "passenger_to_driver"


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint("score BETWEEN 1 AND 5", name="score_range"),
        CheckConstraint(
            "role_context IN ('driver_to_passenger', 'passenger_to_driver')", name="role_context_valid"
        ),
        CheckConstraint("rater_id <> rated_user_id", name="not_self"),
        UniqueConstraint("trip_id", "rater_id", "rated_user_id", name="uq_ratings_trip_rater_rated"),
    )

    rating_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trips.trip_id", ondelete="CASCADE"))
    rater_id: Mapped[uuid.UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE")
    )
    rated_user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDText(), ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    role_context: Mapped[str] = mapped_column(String(32))
    score: Mapped[int] = mapped_column(Integer)
