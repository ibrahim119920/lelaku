# Lelaku Backend

FastAPI + SQLAlchemy (async, asyncpg) + Alembic. Kontrak API untuk frontend ada di [`../integration/`](../integration/README.md).

## Struktur

```text
app/
├── main.py          # FastAPI app, CORS, error handler, registrasi router
├── models.py        # import semua model (dipakai Alembic autogenerate)
├── core/            # config, database session, security (JWT), deps, exceptions
├── auth/            # PLACEHOLDER model users/driver_profiles/vehicles/user_sessions (lihat TODO(auth))
├── trip/            # Trip, Riderequest, Tripmember, Rating (router → service → repository → schemas → models)
└── chat/            # Message
alembic/versions/    # migration, satu per domain
tests/               # test integrasi terhadap Postgres
```

## Menjalankan

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate            # Windows (Git Bash: source .venv/Scripts/activate)
pip install -r requirements-dev.txt
cp .env.example .env              # isi DATABASE_URL, JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

## Test

Test butuh database Postgres **kosong khusus test** (semua tabel di-drop dan dibuat ulang):

```bash
docker run -d --name lelaku-pg-test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=lelaku_test -p 55432:5432 postgres:16-alpine
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_test pytest
```

## Catatan Modul Auth

Modul auth asli dikerjakan terpisah. Sampai kodenya masuk repo:

- `app/auth/models.py` dan migration `0001_auth_placeholder` hanya placeholder sesuai ERD.
- `app/core/security.py::get_current_user_id` membaca JWT (claim `sub` = `user_id`) dari cookie `access_token` atau header `Authorization: Bearer`, ditandatangani `JWT_SECRET` (HS256).

Saat modul auth asli masuk: hapus placeholder, ganti `get_current_user_id`, dan ubah `down_revision` di `0002_trip.py` ke revision terakhir modul auth.
