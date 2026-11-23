# Database PostgreSQL: Supabase sementara, Azure untuk production

Backend menggunakan PostgreSQL standar melalui SQLAlchemy **async** dan driver
**asyncpg**. Supabase adalah provider sementara; aplikasi tidak memakai Supabase
Auth, Supabase SDK, atau fitur database khusus Supabase. Untuk pindah ke Azure
Database for PostgreSQL, pertahankan kode dan ganti nilai `DATABASE_URL` dengan
connection string Azure yang sesuai.

Kode backend berjalan dari folder `backend/`; aplikasi Next.js dan dependency
npm berada di `frontend/`. Konfigurasi lokal dipisah agar URL database tidak
masuk ke environment frontend.

## Menyiapkan koneksi database

1. Siapkan PostgreSQL (lokal, Supabase, atau Azure).
2. Salin `backend/.env.example` menjadi `backend/.env`, lalu isi variabel:

   | Variabel | Keterangan |
   | --- | --- |
   | `DATABASE_URL` | Connection string PostgreSQL. Bentuk `postgresql://` otomatis dinormalisasi ke `postgresql+asyncpg://`; `sslmode=` diubah menjadi `ssl=` untuk asyncpg. |
   | `TEST_DATABASE_URL` | Database **khusus test**. Wajib berbeda dari `DATABASE_URL`; test menghapus seluruh tabel. |
   | `DB_DISABLE_STATEMENT_CACHE` | Set `true` untuk pooler Supabase mode transaction (port `6543`) yang tidak mendukung prepared statement cache. |
   | `APP_ENV` | `development` agar cookie sesi tidak memakai flag `Secure` di `http://localhost`. Nilai lain dianggap production. |
   | `SESSION_COOKIE_NAME` | Nama cookie sesi, default `lelaku_session`. |
   | `SESSION_TTL_SECONDS` | Masa berlaku sesi, 300–2592000 detik (default 7 hari). |
   | `APP_TIMEZONE` | Zona waktu untuk query `date`/`time`, default `Asia/Jakarta`. |
   | `CORS_ORIGINS` | Origin frontend yang boleh mengakses API, dipisah koma. |

3. Jangan memasukkan URI yang berisi password ke Git, issue, atau chat. Buat
   `frontend/.env.local` dari `frontend/.env.example` bila tersedia; jangan
   menaruh `DATABASE_URL` pada environment frontend.
4. Pasang dependency backend dan jalankan migrasi dari folder `backend/`:

   ```powershell
   cd backend
   ..\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   alembic upgrade head
   alembic check
   ```

5. Jalankan API dari folder `backend/`:

   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

6. Di terminal lain, jalankan frontend:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

7. Buka `http://localhost:8000/health/db`. Response sukses:

   ```json
   { "status": "ok", "database": "connected" }
   ```

Endpoint hanya menjalankan `SELECT 1`; endpoint tersebut tidak membuat atau
mengubah tabel. Jika database belum terjangkau, `/health/db` mengembalikan
`503` tanpa membocorkan connection string.

## Database test

Test integrasi memakai Postgres sungguhan dan melakukan `drop_all`/`TRUNCATE`
pada seluruh tabel. Karena itu:

- Isi `TEST_DATABASE_URL` secara eksplisit, baik lewat environment variable
  maupun `backend/.env`.
- Test **tidak pernah** memakai `DATABASE_URL` aplikasi sebagai fallback.
- `conftest.py` menolak host `supabase.co` kecuali `ALLOW_SUPABASE_TEST_DB=1`
  diset. Flag itu hanya boleh dipakai untuk database yang memang khusus test.

Contoh database lokal:

```powershell
# sekali saja, dari klien PostgreSQL (psql)
psql -U postgres -c "CREATE DATABASE lelaku_dev;"
psql -U postgres -c "CREATE DATABASE lelaku_test;"

cd backend
alembic upgrade head
pytest
```

`pytest` membaca `TEST_DATABASE_URL` dari environment atau `backend/.env`.

## Schema

Rantai migrasi berada di `backend/alembic/versions/` dengan revisi `0001`–`0006`:

| Revisi | Isi |
| --- | --- |
| `0001_auth_placeholder` | Tabel `users`, `driver_profiles`, `user_sessions` (versi awal). |
| `0002_trip` | Tabel `trips`, enum `trip_status`. |
| `0003_riderequest_tripmember` | Tabel `ride_requests`, `trip_members`. |
| `0004_message` | Tabel `messages`. |
| `0005_rating` | Tabel `ratings`. |
| `0006_auth_identity` | Auth LL-05 di atas skema UUID: `identity_status`, email unik per `lower(email)`, sesi berkunci hash token, foreign key `ON DELETE CASCADE`. |

Total 10 tabel: `users`, `driver_profiles`, `user_sessions`, `vehicles`,
`trips`, `trip_matches`, `ride_requests`, `trip_members`, `messages`, `ratings`.
Seluruh primary key dan foreign key memakai `uuid`; enum `trip_status` menyimpan
status perjalanan.

Verifikasi:

```powershell
cd backend
alembic current
alembic check
```

`alembic check` membandingkan metadata model dengan schema yang dapat dideteksi
autogenerate. Itu bukan pengganti penerapan migration dan smoke test koneksi
pada server sebenarnya.

## Persiapan perpindahan ke Azure Database for PostgreSQL

Perpindahan ke Azure **belum dilakukan**. Backend dan migration memakai
PostgreSQL standar; tidak ada Supabase SDK, Supabase Auth, atau fitur SQL khusus
Supabase. Migration yang sama dapat diterapkan ke Azure Database for PostgreSQL
tanpa mengubah schema aplikasi.

Sebelum cutover production:

1. Buat server/database Azure PostgreSQL untuk environment tujuan. Samakan major
   version PostgreSQL dengan sumber dan siapkan akses jaringan hanya dari backend
   yang dideploy.
2. Simpan connection string Azure sebagai secret `DATABASE_URL` pada environment
   backend. Jangan taruh password di `NEXT_PUBLIC_*`, source code, log, issue,
   atau file yang masuk Git.
3. Set `APP_ENV=production` agar cookie sesi memakai `Secure`. Untuk koneksi TLS,
   gunakan `sslmode=verify-full` pada connection string; backend mengubahnya
   menjadi `ssl=verify-full` untuk asyncpg. Sediakan CA bundle yang dipercaya
   melalui `sslrootcert` pada connection string atau `PGSSLROOTCERT` di
   environment deployment bila diperlukan.
4. Jalankan Alembic sebagai langkah deployment satu kali sebelum backend mulai
   menerima traffic:

   ```powershell
   cd backend
   alembic upgrade head
   alembic current
   alembic check
   ```

5. Verifikasi `/health/db`, register/login/profile/logout menggunakan akun uji
   khusus environment tersebut, serta pastikan migrasi dan backup berhasil.
6. Jika ada data yang perlu dipindahkan, rencanakan snapshot konsisten, jeda
   penulisan saat cutover, validasi jumlah/relasi data, dan strategi rollback.
   Jangan melakukan dual-write. Jika database masih kosong, cukup terapkan
   migration dan jalankan smoke test sebelum mengganti traffic.
