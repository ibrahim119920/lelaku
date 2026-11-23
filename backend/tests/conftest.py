"""Test integrasi terhadap Postgres sungguhan.

Butuh database kosong khusus test, diatur lewat env TEST_DATABASE_URL, mis.:
    TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_test
Semua tabel di-drop dan dibuat ulang di awal sesi test. JANGAN arahkan ke database development.
"""

import os
import uuid
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

DEFAULT_TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_test"


def reject_unsafe_test_database_url(url: str) -> None:
    """Tolak database bersama (mis. Supabase) karena test menghapus seluruh tabel."""
    host = url.rsplit("@", 1)[-1].split("/", 1)[0].lower()
    if "supabase.co" in host and os.environ.get("ALLOW_SUPABASE_TEST_DB") != "1":
        raise RuntimeError(
            "TEST_DATABASE_URL menunjuk ke Supabase. Test melakukan drop/truncate tabel; "
            "set ALLOW_SUPABASE_TEST_DB=1 hanya jika database itu memang khusus test."
        )


def resolve_test_database_url() -> str:
    """URL database test: env TEST_DATABASE_URL, lalu backend/.env, lalu default lokal.

    Tidak pernah memakai DATABASE_URL aplikasi supaya test tidak menyentuh database development.
    """
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        env_file = Path(__file__).resolve().parents[1] / ".env"
        if env_file.is_file():
            from dotenv import dotenv_values

            url = (dotenv_values(env_file).get("TEST_DATABASE_URL") or "").strip()
    url = url or DEFAULT_TEST_DATABASE_URL
    reject_unsafe_test_database_url(url)
    return url


os.environ["DATABASE_URL"] = resolve_test_database_url()
# Test memakai http://test; cookie `Secure` tidak akan dikirim ulang lewat http.
os.environ["APP_ENV"] = "development"

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.models  # noqa: E402, F401
from app.auth.models import DriverProfile, User, UserSession, Vehicle  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import generate_session_token, hash_session_token  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def _schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS trip_status"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# user_id -> token cookie mentah, diisi oleh make_user() supaya auth() tetap sinkron.
_SESSION_TOKENS: dict[uuid.UUID, str] = {}


@pytest.fixture(autouse=True)
async def _clean_tables():
    yield
    _SESSION_TOKENS.clear()
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def auth(user_id: uuid.UUID) -> dict[str, str]:
    """Header Cookie untuk sesi milik user_id (dibuat oleh make_user).

    User yang tidak dibuat lewat make_user mendapat token acak sehingga ditolak 401.
    """
    token = _SESSION_TOKENS.get(user_id) or generate_session_token()
    return {"Cookie": f"{get_settings().session_cookie_name}={token}"}


async def make_user(name: str = "User", *, driver_status: str | None = None) -> uuid.UUID:
    async with SessionLocal() as session:
        user = User(name=name, email=f"{uuid.uuid4().hex}@test.id", password_hash="x")
        session.add(user)
        await session.flush()
        if driver_status is not None:
            session.add(DriverProfile(user_id=user.user_id, verification_status=driver_status))
        token = generate_session_token()
        session.add(
            UserSession(
                session_token_hash=hash_session_token(token),
                user_id=user.user_id,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        await session.commit()
        _SESSION_TOKENS[user.user_id] = token
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
