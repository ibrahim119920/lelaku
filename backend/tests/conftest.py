"""Trip/chat integration tests use only an explicitly local, disposable Postgres database."""

import os
import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import Header, HTTPException
from sqlalchemy.engine import make_url


_DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@127.0.0.1:55432/"
    "lelaku_test?sslmode=disable"
)
_test_url = make_url(os.environ.get("TEST_DATABASE_URL", _DEFAULT_TEST_DATABASE_URL))
if (
    _test_url.host not in {"localhost", "127.0.0.1", "::1"}
    or not _test_url.database
    or "test" not in _test_url.database.lower()
    or _test_url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}
):
    raise RuntimeError(
        "Trip/chat tests require TEST_DATABASE_URL to point to a local database "
        "whose name contains 'test'."
    )

_test_query = dict(_test_url.query)
_test_query.setdefault("sslmode", "disable")
os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = _test_url.set(
    drivername="postgresql+psycopg",
    query=_test_query,
).render_as_string(hide_password=False)

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import backend.app.models  # noqa: E402, F401
from backend.app.core.database import (  # noqa: E402
    Base,
    get_async_engine,
    get_async_sessionmaker,
)
from backend.app.core.security import get_current_user_id  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.models import DriverProfile, User, Vehicle  # noqa: E402

engine = get_async_engine()
SessionLocal = get_async_sessionmaker()


@pytest.fixture(scope="session", autouse=True)
async def _schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS trip_status"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _clean_tables():
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture(autouse=True)
def _test_identity_dependency():
    def test_identity(x_test_user: str | None = Header(default=None)) -> uuid.UUID:
        if not x_test_user:
            raise HTTPException(status_code=401, detail="Test identity required.")
        try:
            return uuid.UUID(x_test_user)
        except ValueError as error:
            raise HTTPException(status_code=401, detail="Invalid test identity.") from error

    app.dependency_overrides[get_current_user_id] = test_identity
    yield
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def auth(user_id: uuid.UUID | str) -> dict[str, str]:
    return {"X-Test-User": str(user_id)}


async def make_user(name: str = "User", *, driver_status: str | None = None) -> str:
    async with SessionLocal() as session:
        user = User(
            name=name,
            email=f"{uuid.uuid4().hex}@test.id",
            phone="+628123456789",
            password_hash="test-only",
        )
        session.add(user)
        await session.flush()
        if driver_status is not None:
            session.add(DriverProfile(user_id=user.user_id, verification_status=driver_status))
        await session.commit()
        return user.user_id


async def make_vehicle(driver_id: uuid.UUID | str, capacity: int = 4) -> uuid.UUID:
    async with SessionLocal() as session:
        vehicle = Vehicle(
            driver_id=driver_id,
            type="car",
            brand="Toyota",
            model="Avanza",
            plate_number=f"AB {uuid.uuid4().hex[:6]}",
            capacity=capacity,
        )
        session.add(vehicle)
        await session.commit()
        return vehicle.vehicle_id


# Titik-titik di Yogyakarta untuk data test.
UGM = {"lat": -7.7713, "lng": 110.3776}
NEAR_UGM = {"lat": -7.7780, "lng": 110.3800}  # ~0.8 km dari UGM
MALIOBORO = {"lat": -7.7925, "lng": 110.3658}
NEAR_MALIOBORO = {"lat": -7.7990, "lng": 110.3650}  # ~0.7 km dari Malioboro
PRAMBANAN = {"lat": -7.7520, "lng": 110.4915}  # >10 km dari keduanya

WIB = ZoneInfo("Asia/Jakarta")


def future(hours: float = 24) -> datetime:
    return (datetime.now(UTC) + timedelta(hours=hours)).replace(microsecond=0)


def tomorrow_wib(hour: int, minute: int = 0) -> datetime:
    day = datetime.now(WIB).date() + timedelta(days=1)
    return datetime.combine(day, time(hour, minute), tzinfo=WIB)


async def make_trip(
    client: AsyncClient,
    driver_id: uuid.UUID | str,
    vehicle_id: uuid.UUID,
    *,
    origin=UGM,
    destination=MALIOBORO,
    departure: datetime | None = None,
    seats: int = 3,
    cost: float = 10000,
) -> dict:
    resp = await client.post(
        "/trips",
        json={
            "vehicle_id": str(vehicle_id),
            "origin": origin,
            "destination": destination,
            "departure_time": (departure or future()).isoformat(),
            "available_seats": seats,
            "cost_per_seat": cost,
        },
        headers=auth(driver_id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def make_trip_with_passenger(client: AsyncClient, *, seats: int = 3):
    """Trip published milik driver terverifikasi, dengan satu passenger yang sudah di-accept."""
    driver = await make_user("Driver", driver_status="verified")
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle, seats=seats)
    passenger = await make_user("Passenger")
    req = await client.post(
        f"/trips/{trip['trip_id']}/requests",
        json={"pickup": "Gerbang UGM"},
        headers=auth(passenger),
    )
    resp = await client.patch(
        f"/trips/{trip['trip_id']}/requests/{req.json()['request_id']}",
        json={"status": "accepted"},
        headers=auth(driver),
    )
    assert resp.status_code == 200, resp.text
    return driver, passenger, trip
