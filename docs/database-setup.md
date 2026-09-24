# Database PostgreSQL: Supabase sementara, Azure untuk production

Backend menggunakan PostgreSQL standar melalui SQLAlchemy dan driver Psycopg.
Supabase adalah provider sementara; aplikasi tidak memakai Supabase Auth,
Supabase SDK, atau fitur database khusus Supabase. Untuk pindah ke Azure
Database for PostgreSQL, pertahankan kode dan ganti nilai `DATABASE_URL` dengan
connection string Azure yang sesuai.

## Menyiapkan koneksi Supabase lokal

1. Dari Supabase Dashboard, buka proyek lalu pilih **Connect**.
2. Untuk backend FastAPI lokal yang berjalan lama, pilih **Session pooler** jika
   jaringan lokal tidak dapat menjangkau koneksi direct/IPv6. Connection string
   session pooler menggunakan port `5432`. Direct connection juga dapat dipakai
   jika jaringan mendukungnya.
3. Salin connection string dan ganti placeholder password di komputer lokal.
   Jangan memasukkan URI yang berisi password ke Git, issue, atau chat.
4. Buat `.env` di root repo dari `.env.example`, lalu isi `DATABASE_URL` dengan
   URI tersebut. File `.env` sudah diabaikan Git.
5. Pasang dependency backend dan jalankan service dari root repo:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   alembic -c backend\alembic.ini upgrade head
   uvicorn backend.app.main:app --reload --port 8000
   ```

6. Buka `http://localhost:8000/health/db`. Response sukses:

   ```json
   { "status": "ok", "database": "connected" }
   ```

Endpoint hanya menjalankan `SELECT 1`; endpoint tersebut tidak membuat atau
mengubah tabel. Jika `DATABASE_URL` kosong atau database belum terjangkau,
`/health/db` mengembalikan `503` tanpa membocorkan connection string.

## Pindah ke Azure Database for PostgreSQL

Gunakan connection string PostgreSQL dari Azure sebagai `DATABASE_URL` pada
environment deployment, aktifkan SSL sesuai konfigurasi server Azure, lalu
deploy backend yang sama. Jangan menaruh database password di
`NEXT_PUBLIC_*`, source code, atau file yang masuk Git. Gunakan secret
environment milik platform deployment.

## Schema LL-05

Migrasi awal `20260923_0001` membuat tabel PostgreSQL `users`,
`driver_profiles`, dan `user_sessions`, lalu mencatat revisi pada tabel standar
Alembic `alembic_version`. Migrasi mengikuti atribut `USER` dan
`DRIVER_PROFILE` pada ERD, serta penambahan LL-05 yang telah disetujui Bayu.

Penambahan LL-05:

- `users.identity_status`, default `unverified`, dibatasi ke `verified` atau
  `unverified`.
- `user_sessions`, berisi `session_token_hash` (digest token, bukan token
  mentah), `user_id`, `created_at`, `expires_at`, dan `revoked_at`.
- Indeks unik `lower(email)` menolak variasi kapital untuk email yang sama;
  endpoint register tetap perlu memangkas spasi dan menormalisasi email sebelum
  menyimpan.
- Counter agregat dimulai dari nol; constraint mencegah nilai counter negatif.

Belum dibuat pada LL-05: tabel `vehicles`, `trips`, `ride_requests`,
`trip_members`, `trip_matches`, `messages`, dan `ratings`. Tabel-tabel itu
berada di luar ruang lingkup auth/profile. Migrasi dapat diperiksa dengan
`alembic -c backend/alembic.ini current` dan diterapkan pada Azure dengan
connection string Azure yang sama-sama PostgreSQL.

Migrasi ini hanya menyiapkan struktur; endpoint register/login/logout, hashing
password, pemeriksaan session, dan operasi profile masih harus diimplementasikan
di backend sebelum LL-05 dapat dinyatakan selesai.
