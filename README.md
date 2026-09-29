# Lelaku

Lelaku adalah proyek aplikasi perjalanan bersama untuk mempertemukan orang dengan rencana perjalanan yang searah. Produk dirancang mencakup publikasi perjalanan, pencocokan rute dan waktu, titik jemput, permintaan bergabung, percakapan, dan deteksi risiko.

## Status pengembangan

| Bagian | Status di repository |
| --- | --- |
| Registrasi, login, logout, sesi, dan profil | API FastAPI dan antarmuka Next.js sudah diimplementasikan |
| Perjalanan, permintaan bergabung, dan chat | Halaman dan API awal masih berupa placeholder; belum menyimpan data perjalanan |
| Trip matching, rekomendasi titik jemput, dan deteksi risiko | Rancangan produk; belum diimplementasikan |

Detail kebutuhan dan desain ada di [`docs/index.md`](docs/index.md). Tabel ini menggambarkan kode pada branch `develop`, bukan janji bahwa seluruh rancangan produk sudah berjalan.

## Teknologi dan struktur

- `frontend/` — Next.js 15, React 19, dan TypeScript; jalankan perintah npm dari folder ini.
- `backend/` — FastAPI, SQLAlchemy, autentikasi, pengelolaan profil, dan migrasi Alembic untuk PostgreSQL.
- `database/` — direktori cadangan untuk artefak database bersama; migrasi aktif berada di `backend/migrations/`.
- `docs/` — rancangan produk, kontrak autentikasi/profil, dan panduan database.

## Menjalankan secara lokal

Gunakan Python 3.12 dan Node.js 20 seperti pada [CI](.github/workflows/ci.yml), serta database PostgreSQL yang dapat diakses.

1. Salin `backend/.env.example` menjadi `backend/.env` dan isi `DATABASE_URL`. Salin `frontend/.env.example` menjadi `frontend/.env.local`. Jangan taruh kredensial database di variabel `NEXT_PUBLIC_*`.
2. Dari root repository, siapkan backend dan jalankan migrasi:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r backend/requirements.txt
   python -m alembic -c backend/alembic.ini upgrade head
   python -m uvicorn backend.app.main:app --reload --port 8000
   ```

3. Di terminal lain, jalankan frontend:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

4. Buka `http://localhost:3000` untuk aplikasi, `http://localhost:8000/docs` untuk dokumentasi API, dan `http://localhost:8000/health/db` untuk memeriksa koneksi database.

Panduan koneksi Supabase/PostgreSQL, persyaratan TLS, dan rincian migrasi ada di [`docs/database-setup.md`](docs/database-setup.md).

## Pemeriksaan proyek

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Tim

Kelompok **Finished or Not, Submit!**: Ahmad Maulana Ibrahim (24/539655/TK/59853), Bayu Rahmat Kurnia (24/533736/TK/59139), dan Sukmawati (24/545512/TK/60686).
