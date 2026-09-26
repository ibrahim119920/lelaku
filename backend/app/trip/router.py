import uuid
from datetime import date, time

from fastapi import APIRouter, Query, status

from backend.app.core.deps import CurrentUserId, DbSession
from backend.app.trip import service
from backend.app.trip.models import RatingRoleContext, RideRequestStatus, TripStatus
from backend.app.trip.schemas import (
    JoinedTripOut,
    RatingCreate,
    RatingOut,
    ReceivedRatingOut,
    RecommendedTripOut,
    RideRequestCreate,
    RideRequestDecision,
    RideRequestOut,
    RideRequestWithRequesterOut,
    TripCreate,
    TripDetailOut,
    TripMemberOut,
    TripOut,
    TripStatusUpdate,
)

trips_router = APIRouter(prefix="/trips", tags=["trips"])
users_router = APIRouter(prefix="/users", tags=["ratings"])

# ---------- Trip ----------


@trips_router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
async def create_trip(data: TripCreate, session: DbSession, user_id: CurrentUserId):
    return await service.create_trip(session, user_id, data)


@trips_router.get("", response_model=list[TripOut])
async def search_trips(
    session: DbSession,
    _: CurrentUserId,
    origin_lat: float | None = Query(None, ge=-90, le=90),
    origin_lng: float | None = Query(None, ge=-180, le=180),
    destination_lat: float | None = Query(None, ge=-90, le=90),
    destination_lng: float | None = Query(None, ge=-180, le=180),
    on_date: date | None = Query(None, alias="date"),
    at_time: time | None = Query(None, alias="time"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await service.search_trips(
        session,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=destination_lat,
        destination_lng=destination_lng,
        on_date=on_date,
        at_time=at_time,
        limit=limit,
        offset=offset,
    )


# Didefinisikan sebelum /{trip_id} supaya "recommended" dan "me" tidak dianggap trip_id.
@trips_router.get("/recommended", response_model=list[RecommendedTripOut])
async def recommended_trips(trip_id: uuid.UUID, session: DbSession, user_id: CurrentUserId):
    return await service.recommend_trips(session, user_id, trip_id)


@trips_router.get("/me/published", response_model=list[TripOut])
async def my_published_trips(session: DbSession, user_id: CurrentUserId):
    return await service.list_my_published_trips(session, user_id)


@trips_router.get("/me/joined", response_model=list[JoinedTripOut])
async def my_joined_trips(session: DbSession, user_id: CurrentUserId):
    return await service.list_my_joined_trips(session, user_id)


@trips_router.get("/{trip_id}", response_model=TripDetailOut)
async def get_trip(trip_id: uuid.UUID, session: DbSession, _: CurrentUserId):
    return await service.get_trip_detail(session, trip_id)


@trips_router.patch("/{trip_id}/status", response_model=TripOut)
async def update_trip_status(
    trip_id: uuid.UUID, data: TripStatusUpdate, session: DbSession, user_id: CurrentUserId
):
    return await service.update_trip_status(session, user_id, trip_id, TripStatus(data.status))


# ---------- Riderequest ----------


@trips_router.post(
    "/{trip_id}/requests", response_model=RideRequestOut, status_code=status.HTTP_201_CREATED
)
async def create_ride_request(
    trip_id: uuid.UUID, data: RideRequestCreate, session: DbSession, user_id: CurrentUserId
):
    return await service.create_ride_request(session, user_id, trip_id, data)


@trips_router.get("/{trip_id}/requests", response_model=list[RideRequestWithRequesterOut])
async def list_ride_requests(
    trip_id: uuid.UUID,
    session: DbSession,
    user_id: CurrentUserId,
    request_status: RideRequestStatus | None = Query(None, alias="status"),
):
    return await service.list_ride_requests(session, user_id, trip_id, request_status)


@trips_router.patch("/{trip_id}/requests/{request_id}", response_model=RideRequestOut)
async def decide_ride_request(
    trip_id: uuid.UUID,
    request_id: uuid.UUID,
    data: RideRequestDecision,
    session: DbSession,
    user_id: CurrentUserId,
):
    return await service.decide_ride_request(
        session, user_id, trip_id, request_id, RideRequestStatus(data.status)
    )


# ---------- Tripmember ----------


@trips_router.get("/{trip_id}/members", response_model=list[TripMemberOut])
async def list_trip_members(trip_id: uuid.UUID, session: DbSession, _: CurrentUserId):
    return await service.list_trip_members(session, trip_id)


# ---------- Rating ----------


@trips_router.post("/{trip_id}/ratings", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
async def create_rating(trip_id: uuid.UUID, data: RatingCreate, session: DbSession, user_id: CurrentUserId):
    return await service.create_rating(session, user_id, trip_id, data)


@users_router.get("/{user_id}/ratings", response_model=list[ReceivedRatingOut])
async def list_ratings_received(
    user_id: uuid.UUID,
    session: DbSession,
    _: CurrentUserId,
    role_context: RatingRoleContext | None = None,
):
    return await service.list_ratings_received(session, user_id, role_context)
