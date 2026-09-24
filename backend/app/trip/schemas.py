import uuid
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.trip.models import Trip, TripStatus


class LatLng(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


# ---------- Trip ----------


class TripCreate(BaseModel):
    vehicle_id: uuid.UUID
    origin: LatLng
    destination: LatLng
    departure_time: AwareDatetime = Field(description="ISO 8601 dengan offset, mis. 2026-10-01T07:30:00+07:00")
    available_seats: int = Field(ge=1)
    cost_per_seat: float = Field(ge=0)


class TripStatusUpdate(BaseModel):
    status: Literal["ongoing", "completed", "cancelled"]


class TripOut(BaseModel):
    trip_id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    origin: LatLng
    destination: LatLng
    departure_time: datetime
    available_seats: int
    status: TripStatus
    estimated_total_cost: float
    cost_per_seat: float

    @classmethod
    def from_model(cls, trip: Trip) -> "TripOut":
        return cls(
            trip_id=trip.trip_id,
            driver_id=trip.driver_id,
            vehicle_id=trip.vehicle_id,
            origin=LatLng(lat=trip.origin_lat, lng=trip.origin_lng),
            destination=LatLng(lat=trip.destination_lat, lng=trip.destination_lng),
            departure_time=trip.departure_time,
            available_seats=trip.available_seats,
            status=trip.status,
            estimated_total_cost=trip.estimated_total_cost,
            cost_per_seat=trip.cost_per_seat,
        )


class DriverInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    profile_photo: str | None
    avg_rating_driver: float
    total_ratings_driver: int


class VehicleInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: uuid.UUID
    type: str
    brand: str
    model: str
    plate_number: str
    capacity: int


class TripDetailOut(TripOut):
    driver: DriverInfo
    vehicle: VehicleInfo


class RecommendedTripOut(BaseModel):
    trip: TripOut
    origin_distance_km: float
    destination_distance_km: float
    time_diff_minutes: float
    score: float


class JoinedTripOut(TripOut):
    member_status: str


# ---------- Riderequest ----------


class RideRequestCreate(BaseModel):
    pickup: str = Field(min_length=1, max_length=255, description="Titik jemput, mis. alamat atau 'lat,lng'")


class RideRequestDecision(BaseModel):
    status: Literal["accepted", "rejected"]


class RideRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: uuid.UUID
    trip_id: uuid.UUID
    requester_id: uuid.UUID
    pickup: str
    status: str
    created_at: datetime


class RequesterInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    profile_photo: str | None
    avg_rating: float
    total_ratings: int


class RideRequestWithRequesterOut(RideRequestOut):
    requester: RequesterInfo


# ---------- Tripmember ----------


class TripMemberOut(BaseModel):
    user_id: uuid.UUID
    name: str
    profile_photo: str | None
    role: Literal["driver", "passenger"]
    trip_member_id: uuid.UUID | None = Field(description="null untuk driver (anggota implisit)")
    status: str


# ---------- Rating ----------


class RatingCreate(BaseModel):
    rated_user_id: uuid.UUID
    role_context: Literal["driver_to_passenger", "passenger_to_driver"]
    score: int = Field(ge=1, le=5, strict=True)


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating_id: uuid.UUID
    trip_id: uuid.UUID
    rater_id: uuid.UUID
    rated_user_id: uuid.UUID
    role_context: str
    score: int


class ReceivedRatingOut(RatingOut):
    rater_name: str
    trip_departure_time: datetime
