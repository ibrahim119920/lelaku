import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.trip import matching
from app.trip import repository as repo
from app.trip.models import (
    Rating,
    RatingRoleContext,
    RideRequest,
    RideRequestStatus,
    Trip,
    TripMember,
    TripMemberStatus,
    TripStatus,
)
from app.trip.schemas import (
    DriverInfo,
    JoinedTripOut,
    RatingCreate,
    RatingOut,
    ReceivedRatingOut,
    RecommendedTripOut,
    RequesterInfo,
    RideRequestCreate,
    RideRequestOut,
    RideRequestWithRequesterOut,
    TripCreate,
    TripDetailOut,
    TripMemberOut,
    TripOut,
    VehicleInfo,
)

# ---------- Trip ----------

# Transisi manual oleh driver; tidak bisa lompat atau mundur.
ALLOWED_STATUS_TRANSITIONS: dict[TripStatus, set[TripStatus]] = {
    TripStatus.published: {TripStatus.ongoing, TripStatus.cancelled},
    TripStatus.ongoing: {TripStatus.completed, TripStatus.cancelled},
    TripStatus.completed: set(),
    TripStatus.cancelled: set(),
}


async def get_trip_or_404(session: AsyncSession, trip_id: uuid.UUID, *, for_update: bool = False) -> Trip:
    trip = await repo.get_trip(session, trip_id, for_update=for_update)
    if trip is None:
        raise NotFoundError("Trip tidak ditemukan.")
    return trip


async def create_trip(session: AsyncSession, user_id: uuid.UUID, data: TripCreate) -> TripOut:
    profile = await repo.get_driver_profile(session, user_id)
    if profile is None or profile.verification_status != "verified":
        raise ForbiddenError("Hanya driver terverifikasi yang bisa mempublikasikan trip.")

    vehicle = await repo.get_vehicle(session, data.vehicle_id)
    if vehicle is None:
        raise NotFoundError("Kendaraan tidak ditemukan.")
    if vehicle.driver_id != user_id:
        raise ForbiddenError("Kendaraan ini bukan milikmu.")
    if data.available_seats > vehicle.capacity:
        raise BadRequestError(f"available_seats melebihi kapasitas kendaraan ({vehicle.capacity}).")
    if data.departure_time <= datetime.now(UTC):
        raise BadRequestError("departure_time harus di masa depan.")

    trip = Trip(
        driver_id=user_id,
        vehicle_id=vehicle.vehicle_id,
        origin_lat=data.origin.lat,
        origin_lng=data.origin.lng,
        destination_lat=data.destination.lat,
        destination_lng=data.destination.lng,
        departure_time=data.departure_time,
        available_seats=data.available_seats,
        status=TripStatus.published,
        cost_per_seat=data.cost_per_seat,
        estimated_total_cost=data.cost_per_seat * data.available_seats,
    )
    repo.add_trip(session, trip)
    await session.commit()
    return TripOut.from_model(trip)


def _search_window(on_date: date | None, at_time: time | None) -> tuple[datetime | None, datetime | None]:
    if at_time is not None and on_date is None:
        raise BadRequestError("Parameter time harus disertai date.")
    if on_date is None:
        return None, None
    tz = get_settings().tz
    if at_time is None:
        start = datetime.combine(on_date, time.min, tzinfo=tz)
        return start, start + timedelta(days=1) - timedelta(microseconds=1)
    return matching.time_window(datetime.combine(on_date, at_time, tzinfo=tz))


def _point_pair(lat: float | None, lng: float | None, name: str) -> tuple[float, float] | None:
    if (lat is None) != (lng is None):
        raise BadRequestError(f"{name}_lat dan {name}_lng harus diisi bersamaan.")
    return None if lat is None else (lat, lng)


async def search_trips(
    session: AsyncSession,
    *,
    origin_lat: float | None,
    origin_lng: float | None,
    destination_lat: float | None,
    destination_lng: float | None,
    on_date: date | None,
    at_time: time | None,
    limit: int,
    offset: int,
) -> list[TripOut]:
    origin = _point_pair(origin_lat, origin_lng, "origin")
    destination = _point_pair(destination_lat, destination_lng, "destination")
    departure_from, departure_to = _search_window(on_date, at_time)
    radius = matching.MATCH_DISTANCE_THRESHOLD_KM

    candidates = await repo.find_trip_candidates(
        session,
        status=TripStatus.published,
        departure_from=departure_from,
        departure_to=departure_to,
        origin_box=matching.bounding_box(*origin, radius) if origin else None,
        destination_box=matching.bounding_box(*destination, radius) if destination else None,
    )
    results = [
        trip
        for trip in candidates
        if (origin is None or matching.haversine_km(*origin, trip.origin_lat, trip.origin_lng) <= radius)
        and (
            destination is None
            or matching.haversine_km(*destination, trip.destination_lat, trip.destination_lng) <= radius
        )
    ]
    return [TripOut.from_model(trip) for trip in results[offset : offset + limit]]


async def recommend_trips(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID
) -> list[RecommendedTripOut]:
    ref = await get_trip_or_404(session, trip_id)
    radius = matching.MATCH_DISTANCE_THRESHOLD_KM
    departure_from, departure_to = matching.time_window(ref.departure_time)

    candidates = await repo.find_trip_candidates(
        session,
        status=TripStatus.published,
        departure_from=departure_from,
        departure_to=departure_to,
        origin_box=matching.bounding_box(ref.origin_lat, ref.origin_lng, radius),
        destination_box=matching.bounding_box(ref.destination_lat, ref.destination_lng, radius),
        exclude_trip_id=ref.trip_id,
        exclude_driver_id=user_id,
    )

    recommendations: list[RecommendedTripOut] = []
    for trip in candidates:
        origin_km = matching.haversine_km(ref.origin_lat, ref.origin_lng, trip.origin_lat, trip.origin_lng)
        destination_km = matching.haversine_km(
            ref.destination_lat, ref.destination_lng, trip.destination_lat, trip.destination_lng
        )
        if origin_km > radius or destination_km > radius:
            continue
        time_diff = trip.departure_time - ref.departure_time
        recommendations.append(
            RecommendedTripOut(
                trip=TripOut.from_model(trip),
                origin_distance_km=round(origin_km, 3),
                destination_distance_km=round(destination_km, 3),
                time_diff_minutes=round(abs(time_diff).total_seconds() / 60, 1),
                score=matching.match_score(origin_km, destination_km, time_diff),
            )
        )
    recommendations.sort(key=lambda r: r.score, reverse=True)
    return recommendations


async def get_trip_detail(session: AsyncSession, trip_id: uuid.UUID) -> TripDetailOut:
    row = await repo.get_trip_detail(session, trip_id)
    if row is None:
        raise NotFoundError("Trip tidak ditemukan.")
    trip, driver, profile, vehicle = row
    return TripDetailOut(
        **TripOut.from_model(trip).model_dump(),
        driver=DriverInfo(
            user_id=driver.user_id,
            name=driver.name,
            profile_photo=driver.profile_photo,
            avg_rating_driver=profile.avg_rating_driver if profile else 0,
            total_ratings_driver=profile.total_ratings_driver if profile else 0,
        ),
        vehicle=VehicleInfo.model_validate(vehicle),
    )


async def list_my_published_trips(session: AsyncSession, user_id: uuid.UUID) -> list[TripOut]:
    return [TripOut.from_model(trip) for trip in await repo.list_trips_by_driver(session, user_id)]


async def list_my_joined_trips(session: AsyncSession, user_id: uuid.UUID) -> list[JoinedTripOut]:
    return [
        JoinedTripOut(**TripOut.from_model(trip).model_dump(), member_status=member_status)
        for trip, member_status in await repo.list_joined_trips(session, user_id)
    ]


async def update_trip_status(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, new_status: TripStatus
) -> TripOut:
    trip = await get_trip_or_404(session, trip_id, for_update=True)
    if trip.driver_id != user_id:
        raise ForbiddenError("Hanya driver pemilik trip yang bisa mengubah status.")
    if new_status not in ALLOWED_STATUS_TRANSITIONS[trip.status]:
        raise ConflictError(f"Transisi status dari '{trip.status.value}' ke '{new_status.value}' tidak diizinkan.")

    trip.status = new_status
    if new_status == TripStatus.cancelled:
        await repo.cancel_trip_members(session, trip.trip_id)
    await session.commit()
    return TripOut.from_model(trip)


# ---------- Riderequest ----------


async def create_ride_request(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, data: RideRequestCreate
) -> RideRequestOut:
    trip = await get_trip_or_404(session, trip_id)
    if trip.driver_id == user_id:
        raise ForbiddenError("Driver tidak bisa mengajukan request ke trip miliknya sendiri.")
    if trip.status != TripStatus.published:
        raise ConflictError("Trip sudah tidak menerima permintaan bergabung.")
    if trip.available_seats <= 0:
        raise ConflictError("Kursi trip sudah penuh.")
    if await repo.get_active_request(session, trip_id, user_id) is not None:
        raise ConflictError("Kamu sudah punya request yang masih pending atau sudah diterima di trip ini.")

    ride_request = RideRequest(trip_id=trip_id, requester_id=user_id, pickup=data.pickup)
    repo.add(session, ride_request)
    try:
        await session.commit()
    except IntegrityError:
        # Dua request bersamaan dari user yang sama: ditangkap partial unique index.
        await session.rollback()
        raise ConflictError("Kamu sudah punya request yang masih pending atau sudah diterima di trip ini.")
    await session.refresh(ride_request)
    return RideRequestOut.model_validate(ride_request)


async def _get_own_trip(session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, *, for_update: bool = False) -> Trip:
    trip = await get_trip_or_404(session, trip_id, for_update=for_update)
    if trip.driver_id != user_id:
        raise ForbiddenError("Hanya driver pemilik trip yang bisa mengakses request trip ini.")
    return trip


async def list_ride_requests(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, status: RideRequestStatus | None
) -> list[RideRequestWithRequesterOut]:
    await _get_own_trip(session, user_id, trip_id)
    return [
        RideRequestWithRequesterOut(
            **RideRequestOut.model_validate(ride_request).model_dump(),
            requester=RequesterInfo.model_validate(requester),
        )
        for ride_request, requester in await repo.list_requests_for_trip(session, trip_id, status)
    ]


async def decide_ride_request(
    session: AsyncSession,
    user_id: uuid.UUID,
    trip_id: uuid.UUID,
    request_id: uuid.UUID,
    decision: RideRequestStatus,
) -> RideRequestOut:
    # Kunci baris trip supaya dua accept bersamaan tidak membuat available_seats negatif.
    trip = await _get_own_trip(session, user_id, trip_id, for_update=True)
    ride_request = await repo.get_request(session, trip_id, request_id, for_update=True)
    if ride_request is None:
        raise NotFoundError("Request tidak ditemukan di trip ini.")
    if ride_request.status != RideRequestStatus.pending.value:
        raise ConflictError(f"Request sudah diproses (status: {ride_request.status}).")

    if decision == RideRequestStatus.accepted:
        if trip.status != TripStatus.published:
            raise ConflictError("Request hanya bisa diterima selama trip berstatus published.")
        if trip.available_seats <= 0:
            raise ConflictError("Kursi trip sudah habis, request tidak bisa diterima.")
        trip.available_seats -= 1
        repo.add(
            session,
            TripMember(
                trip_id=trip_id,
                user_id=ride_request.requester_id,
                ride_request_id=ride_request.request_id,
                status=TripMemberStatus.active.value,
            ),
        )

    ride_request.status = decision.value
    await session.commit()
    return RideRequestOut.model_validate(ride_request)


# ---------- Tripmember ----------


async def list_trip_members(session: AsyncSession, trip_id: uuid.UUID) -> list[TripMemberOut]:
    trip = await get_trip_or_404(session, trip_id)
    driver = await repo.get_user(session, trip.driver_id)
    members = [
        TripMemberOut(
            user_id=driver.user_id,
            name=driver.name,
            profile_photo=driver.profile_photo,
            role="driver",
            trip_member_id=None,
            status=TripMemberStatus.active.value,
        )
    ]
    members += [
        TripMemberOut(
            user_id=user.user_id,
            name=user.name,
            profile_photo=user.profile_photo,
            role="passenger",
            trip_member_id=member.trip_member_id,
            status=member.status,
        )
        for member, user in await repo.list_trip_members(session, trip_id)
    ]
    return members


async def is_trip_participant(session: AsyncSession, trip: Trip, user_id: uuid.UUID) -> bool:
    """Driver pemilik trip atau passenger yang Tripmember-nya masih active."""
    return trip.driver_id == user_id or await repo.is_active_member(session, trip.trip_id, user_id)


# ---------- Rating ----------


async def create_rating(
    session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID, data: RatingCreate
) -> RatingOut:
    trip = await get_trip_or_404(session, trip_id)
    if trip.status != TripStatus.completed:
        raise ConflictError("Rating hanya bisa diberikan setelah trip berstatus completed.")
    if not await is_trip_participant(session, trip, user_id):
        raise ForbiddenError("Hanya anggota trip yang bisa memberi rating.")
    if data.rated_user_id == user_id:
        raise BadRequestError("Tidak bisa memberi rating ke diri sendiri.")

    role_context = RatingRoleContext(data.role_context)
    if role_context == RatingRoleContext.driver_to_passenger:
        if trip.driver_id != user_id or not await repo.is_active_member(session, trip_id, data.rated_user_id):
            raise BadRequestError(
                "driver_to_passenger: pemberi harus driver trip dan penerima harus passenger trip ini."
            )
    elif trip.driver_id != data.rated_user_id:
        raise BadRequestError("passenger_to_driver: penerima harus driver trip ini.")

    # Kunci baris user penerima supaya rating bersamaan tidak saling menimpa agregat.
    rated_user = await repo.get_user_for_update(session, data.rated_user_id)
    if rated_user is None:
        raise NotFoundError("User yang dirating tidak ditemukan.")
    if await repo.rating_exists(session, trip_id, user_id, data.rated_user_id):
        raise ConflictError("Kamu sudah memberi rating ke user ini untuk trip ini.")

    rating = Rating(
        trip_id=trip_id,
        rater_id=user_id,
        rated_user_id=data.rated_user_id,
        role_context=role_context.value,
        score=data.score,
    )
    repo.add(session, rating)
    await session.flush()

    # Agregat dipisah per peran: sebagai passenger di users, sebagai driver di driver_profiles.
    avg, count = await repo.rating_aggregate(session, data.rated_user_id, role_context)
    if role_context == RatingRoleContext.driver_to_passenger:
        rated_user.avg_rating, rated_user.total_ratings = avg, count
    else:
        profile = await repo.get_driver_profile(session, data.rated_user_id)
        if profile is not None:
            profile.avg_rating_driver, profile.total_ratings_driver = avg, count

    await session.commit()
    return RatingOut.model_validate(rating)


async def list_ratings_received(
    session: AsyncSession, user_id: uuid.UUID, role_context: RatingRoleContext | None
) -> list[ReceivedRatingOut]:
    if await repo.get_user(session, user_id) is None:
        raise NotFoundError("User tidak ditemukan.")
    return [
        ReceivedRatingOut(
            **RatingOut.model_validate(rating).model_dump(),
            rater_name=rater_name,
            trip_departure_time=departure_time,
        )
        for rating, rater_name, departure_time in await repo.list_ratings_received(session, user_id, role_context)
    ]
