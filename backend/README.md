# Lelaku Backend

FastAPI + SQLAlchemy (async, asyncpg) + Alembic. Kontrak API untuk frontend ada di [`../integration/`](../integration/README.md).

## Struktur

```text
app/
├── main.py          # FastAPI app, CORS, error handler, registrasi router
├── models.py        # import semua model (dipakai Alembic autogenerate)
├── core/            # config, database session, security (JWT), deps, exceptions
├── auth/            # register/login/logout, profil, sesi cookie (router → service → repository → schemas → models)
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

Auth memakai **sesi server-side**: login mengirim cookie `lelaku_session` (HttpOnly) berisi token opaque, dan database hanya menyimpan hash SHA-256-nya (`user_sessions`). Password di-hash Argon2 di threadpool. Kontrak endpoint: [`../integration-docs/auth-api.md`](../integration-docs/auth-api.md).

- `app/auth/deps.py::get_current_user` adalah satu-satunya tempat sesi divalidasi; modul trip/chat memakai `CurrentUserId` (`app/core/deps.py`).
- Set `APP_ENV=development` di `.env` untuk dev lokal. Selain itu cookie memakai flag `Secure` dan butuh HTTPS.
- Jalankan `alembic upgrade head` (sampai `0006_auth_identity`). Test memakai `create_all`, jadi migration perlu dicoba terpisah di database kosong.
- `Vehicle` masih placeholder (belum ada modul/endpoint kendaraan).
- Belum ada: rate limiting login, pembersihan sesi kedaluwarsa, upload dokumen identitas (FR-03).
