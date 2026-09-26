import uuid
from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import DriverProfile, User, Vehicle
from backend.app.trip.models import (
    Rating,
    RatingRoleContext,
    RideRequest,
    RideRequestStatus,
    Trip,
    TripMember,
    TripMemberStatus,
    TripStatus,
)

# ---------- Trip ----------


async def get_trip(session: AsyncSession, trip_id: uuid.UUID, *, for_update: bool = False) -> Trip | None:
    stmt = select(Trip).where(Trip.trip_id == trip_id)
    if for_update:
        stmt = stmt.with_for_update()
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_trip_detail(
    session: AsyncSession, trip_id: uuid.UUID
) -> tuple[Trip, User, DriverProfile | None, Vehicle] | None:
    stmt = (
        select(Trip, User, DriverProfile, Vehicle)
        .join(User, User.user_id == Trip.driver_id)
        .outerjoin(DriverProfile, DriverProfile.user_id == Trip.driver_id)
        .join(Vehicle, Vehicle.vehicle_id == Trip.vehicle_id)
        .where(Trip.trip_id == trip_id)
    )
    row = (await session.execute(stmt)).one_or_none()
    return tuple(row) if row else None


async def get_vehicle(session: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle | None:
    return await session.get(Vehicle, vehicle_id)


async def get_driver_profile(session: AsyncSession, user_id: uuid.UUID) -> DriverProfile | None:
    return await session.get(DriverProfile, str(user_id))


def add_trip(session: AsyncSession, trip: Trip) -> None:
    session.add(trip)


def _within_box(stmt: Select, lat_col, lng_col, box: tuple[float, float, float, float]) -> Select:
    min_lat, max_lat, min_lng, max_lng = box
    return stmt.where(lat_col.between(min_lat, max_lat), lng_col.between(min_lng, max_lng))


async def find_trip_candidates(
    session: AsyncSession,
    *,
    status: TripStatus,
    departure_from: datetime | None = None,
    departure_to: datetime | None = None,
    origin_box: tuple[float, float, float, float] | None = None,
    destination_box: tuple[float, float, float, float] | None = None,
    exclude_trip_id: uuid.UUID | None = None,
    exclude_driver_id: uuid.UUID | None = None,
) -> list[Trip]:
    """Prefilter kasar di SQL; filter radius presisi (Haversine) dilakukan di service."""
    stmt = select(Trip).where(Trip.status == status)
    if departure_from is not None:
        stmt = stmt.where(Trip.departure_time >= departure_from)
    if departure_to is not None:
        stmt = stmt.where(Trip.departure_time <= departure_to)
    if origin_box is not None:
        stmt = _within_box(stmt, Trip.origin_lat, Trip.origin_lng, origin_box)
    if destination_box is not None:
        stmt = _within_box(stmt, Trip.destination_lat, Trip.destination_lng, destination_box)
    if exclude_trip_id is not None:
        stmt = stmt.where(Trip.trip_id != exclude_trip_id)
    if exclude_driver_id is not None:
        stmt = stmt.where(Trip.driver_id != exclude_driver_id)
    stmt = stmt.order_by(Trip.departure_time)
    return list((await session.execute(stmt)).scalars())


async def list_trips_by_driver(session: AsyncSession, driver_id: uuid.UUID) -> list[Trip]:
    stmt = select(Trip).where(Trip.driver_id == driver_id).order_by(Trip.departure_time.desc())
    return list((await session.execute(stmt)).scalars())


async def list_joined_trips(session: AsyncSession, user_id: uuid.UUID) -> list[tuple[Trip, str]]:
    stmt = (
        select(Trip, TripMember.status)
        .join(TripMember, TripMember.trip_id == Trip.trip_id)
        .where(TripMember.user_id == user_id)
        .order_by(Trip.departure_time.desc())
    )
    return [tuple(row) for row in await session.execute(stmt)]


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, str(user_id))


# ---------- Riderequest ----------


async def get_active_request(
    session: AsyncSession, trip_id: uuid.UUID, requester_id: uuid.UUID
) -> RideRequest | None:
    stmt = select(RideRequest).where(
        RideRequest.trip_id == trip_id,
        RideRequest.requester_id == requester_id,
        RideRequest.status.in_([RideRequestStatus.pending.value, RideRequestStatus.accepted.value]),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_request(
    session: AsyncSession, trip_id: uuid.UUID, request_id: uuid.UUID, *, for_update: bool = False
) -> RideRequest | None:
    stmt = select(RideRequest).where(RideRequest.request_id == request_id, RideRequest.trip_id == trip_id)
    if for_update:
        stmt = stmt.with_for_update()
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_requests_for_trip(
    session: AsyncSession, trip_id: uuid.UUID, status: RideRequestStatus | None = None
) -> list[tuple[RideRequest, User]]:
    stmt = (
        select(RideRequest, User)
        .join(User, User.user_id == RideRequest.requester_id)
        .where(RideRequest.trip_id == trip_id)
        .order_by(RideRequest.created_at)
    )
    if status is not None:
        stmt = stmt.where(RideRequest.status == status.value)
    return [tuple(row) for row in await session.execute(stmt)]


def add(session: AsyncSession, obj: object) -> None:
    session.add(obj)


# ---------- Tripmember ----------


async def list_trip_members(session: AsyncSession, trip_id: uuid.UUID) -> list[tuple[TripMember, User]]:
    stmt = (
        select(TripMember, User)
        .join(User, User.user_id == TripMember.user_id)
        .join(RideRequest, RideRequest.request_id == TripMember.ride_request_id)
        .where(TripMember.trip_id == trip_id)
        .order_by(RideRequest.created_at)
    )
    return [tuple(row) for row in await session.execute(stmt)]


async def is_active_member(session: AsyncSession, trip_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    stmt = select(TripMember.trip_member_id).where(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id,
        TripMember.status == TripMemberStatus.active.value,
    )
    return (await session.execute(stmt)).first() is not None


async def cancel_trip_members(session: AsyncSession, trip_id: uuid.UUID) -> None:
    await session.execute(
        update(TripMember)
        .where(TripMember.trip_id == trip_id, TripMember.status == TripMemberStatus.active.value)
        .values(status=TripMemberStatus.cancelled.value)
    )


# ---------- Rating ----------


async def get_user_for_update(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    stmt = select(User).where(User.user_id == str(user_id)).with_for_update()
    return (await session.execute(stmt)).scalar_one_or_none()


async def rating_exists(
    session: AsyncSession, trip_id: uuid.UUID, rater_id: uuid.UUID, rated_user_id: uuid.UUID
) -> bool:
    stmt = select(Rating.rating_id).where(
        Rating.trip_id == trip_id, Rating.rater_id == rater_id, Rating.rated_user_id == rated_user_id
    )
    return (await session.execute(stmt)).first() is not None


async def rating_aggregate(
    session: AsyncSession, rated_user_id: uuid.UUID, role_context: RatingRoleContext
) -> tuple[float, int]:
    stmt = select(func.coalesce(func.avg(Rating.score), 0), func.count(Rating.rating_id)).where(
        Rating.rated_user_id == rated_user_id, Rating.role_context == role_context.value
    )
    avg, count = (await session.execute(stmt)).one()
    return float(avg), int(count)


async def list_ratings_received(
    session: AsyncSession, user_id: uuid.UUID, role_context: RatingRoleContext | None
) -> list[tuple[Rating, str, datetime]]:
    stmt = (
        select(Rating, User.name, Trip.departure_time)
        .join(User, User.user_id == Rating.rater_id)
        .join(Trip, Trip.trip_id == Rating.trip_id)
        .where(Rating.rated_user_id == user_id)
        .order_by(Trip.departure_time.desc())
    )
    if role_context is not None:
        stmt = stmt.where(Rating.role_context == role_context.value)
    return [tuple(row) for row in await session.execute(stmt)]
