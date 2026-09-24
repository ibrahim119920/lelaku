"""Test integrasi terhadap Postgres sungguhan.

Butuh database kosong khusus test, diatur lewat env TEST_DATABASE_URL, mis.:
    TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_test
Semua tabel di-drop dan dibuat ulang di awal sesi test. JANGAN arahkan ke database development.
"""

import os
import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_test"
)

import jwt  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.models  # noqa: E402, F401
from app.auth.models import DriverProfile, User, Vehicle  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


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


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def auth(user_id: uuid.UUID) -> dict[str, str]:
    settings = get_settings()
    token = jwt.encode({"sub": str(user_id)}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return {"Authorization": f"Bearer {token}"}


async def make_user(name: str = "User", *, driver_status: str | None = None) -> uuid.UUID:
    async with SessionLocal() as session:
        user = User(name=name, email=f"{uuid.uuid4().hex}@test.id", password_hash="x")
        session.add(user)
        await session.flush()
        if driver_status is not None:
            session.add(DriverProfile(user_id=user.user_id, verification_status=driver_status))
        await session.commit()
        return user.user_id


async def make_vehicle(driver_id: uuid.UUID, capacity: int = 4) -> uuid.UUID:
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
    driver_id: uuid.UUID,
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
        f"/trips/{trip['trip_id']}/requests", json={"pickup": "Gerbang UGM"}, headers=auth(passenger)
    )
    resp = await client.patch(
        f"/trips/{trip['trip_id']}/requests/{req.json()['request_id']}",
        json={"status": "accepted"},
        headers=auth(driver),
    )
    assert resp.status_code == 200, resp.text
    return driver, passenger, trip
