"""Import semua model supaya terdaftar di Base.metadata (dipakai Alembic)."""

from app.auth.models import DriverProfile, User, UserSession, Vehicle  # noqa: F401
from app.trip.models import Rating, RideRequest, Trip, TripMatch, TripMember  # noqa: F401
from app.chat.models import Message  # noqa: F401
