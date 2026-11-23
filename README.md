# lelaku

Lelaku memungkinkan pengguna mempublikasikan rencana perjalanan dan menemukan teman seperjalanan melalui intelligent trip matching. Sistem merekomendasikan titik pickup yang efisien, mendukung permintaan perjalanan bersama, serta menggunakan AI-assisted risk detection untuk mendeteksi aktivitas mencurigakan.

Kelompok Finished or not, submit!

1. Ketua Kelompok: Ahmad Maulana Ibrahim-24/539655/TK/59853
2. Anggota 1: BAYU RAHMAT KURNIA - 24/533736/TK/59139
3. Anggota 2: Sukmawati - 24/545512/TK/60686

## Struktur repository

- `frontend/` — aplikasi Next.js. Jalankan perintah npm dari folder ini.
- `backend/` — API FastAPI, autentikasi, dan migrasi PostgreSQL.
- `database/` — artefak database bersama.
- `docs/` — kontrak API, ERD, dan panduan setup.

Instruksi koneksi PostgreSQL dan menjalankan layanan ada di
[`docs/database-setup.md`](docs/database-setup.md).

## Stack

- Frontend: Next.js (`frontend/`)
- Backend: FastAPI + SQLAlchemy async + asyncpg + Alembic (`backend/`)
- Database: PostgreSQL (Supabase sementara, Azure untuk production)

## Menjalankan

```powershell
# backend
cd backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env   # isi DATABASE_URL dan TEST_DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# frontend (terminal lain)
cd frontend
npm ci
npm run dev
```

API berjalan di `http://localhost:8000`, dokumentasi interaktif di
`http://localhost:8000/docs`, dan frontend di `http://localhost:3000`.

## Test

```powershell
cd backend
pytest
```

Test membutuhkan `TEST_DATABASE_URL` yang menunjuk ke database khusus test;
database development/Supabase akan ditolak. Detail: [`docs/database-setup.md`](docs/database-setup.md).

## Dokumentasi

- [`docs/dokumentasi-proyek.md`](docs/dokumentasi-proyek.md) — workflow, UI/UX, ERD
- [`docs/database-setup.md`](docs/database-setup.md) — database, migrasi, Azure
- [`docs/auth-profile-contract.md`](docs/auth-profile-contract.md) — kontrak auth/profile
- [`integration-docs/`](integration-docs/README.md) — kontrak API kanonik
