# Database PostgreSQL: Supabase sementara, Azure untuk production

Backend menggunakan PostgreSQL standar melalui SQLAlchemy dan driver Psycopg.
Supabase adalah provider sementara; aplikasi tidak memakai Supabase Auth,
Supabase SDK, atau fitur database khusus Supabase. Untuk pindah ke Azure
Database for PostgreSQL, pertahankan kode dan ganti nilai `DATABASE_URL` dengan
connection string Azure yang sesuai.

Kode backend berjalan dari folder `backend/`; aplikasi Next.js dan dependency
npm berada di `frontend/`. Konfigurasi lokal dipisah agar URL database tidak
masuk ke environment frontend.

## Menyiapkan koneksi Supabase lokal

1. Dari Supabase Dashboard, buka proyek lalu pilih **Connect**.
2. Untuk backend FastAPI lokal yang berjalan lama, pilih **Session pooler** jika
   jaringan lokal tidak dapat menjangkau koneksi direct/IPv6. Connection string
   session pooler menggunakan port `5432`. Direct connection juga dapat dipakai
   jika jaringan mendukungnya.
3. Salin connection string dan ganti placeholder password di komputer lokal.
   Jangan memasukkan URI yang berisi password ke Git, issue, atau chat.
4. Buat `backend/.env` dari `backend/.env.example`, lalu isi `DATABASE_URL`
   dengan URI tersebut. Buat `frontend/.env.local` dari
   `frontend/.env.example`. Kedua file lokal ini diabaikan Git. Backend masih
   menerima `.env` lama di root repo sebagai fallback selama transisi; jangan
   menaruh `DATABASE_URL` pada file environment frontend.
5. Pasang dependency backend dan jalankan API dari root repo:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   python -m alembic -c backend\alembic.ini upgrade head
   python -m uvicorn backend.app.main:app --reload --port 8000
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
mengubah tabel. Jika `DATABASE_URL` kosong atau database belum terjangkau,
`/health/db` mengembalikan `503` tanpa membocorkan connection string.

## Persiapan perpindahan ke Azure Database for PostgreSQL

Perpindahan ke Azure **belum dilakukan**. Backend dan migration memakai
PostgreSQL standar melalui Psycopg; tidak ada Supabase SDK, Supabase Auth, atau
fitur SQL khusus Supabase. Karena itu, migration yang sama dapat diterapkan ke
Azure Database for PostgreSQL tanpa mengubah schema aplikasi.

Sebelum cutover production:

1. Buat server/database Azure PostgreSQL untuk environment tujuan. Samakan major
   version PostgreSQL dengan sumber dan siapkan akses jaringan hanya dari backend
   yang dideploy.
2. Simpan connection string Azure sebagai secret `DATABASE_URL` pada environment
   backend. Jangan taruh password di `NEXT_PUBLIC_*`, source code, log, issue,
   atau file yang masuk Git. Set `APP_ENV=production`; environment staging dan
   production wajib memakai `sslmode=verify-full`, yang memverifikasi TLS,
   Certificate Authority, dan kecocokan hostname. Sediakan CA bundle yang
   dipercaya oleh libpq melalui `sslrootcert` pada connection string atau
   `PGSSLROOTCERT` di environment deployment. Mode `require`, `verify-ca`,
   `disable`, `allow`, dan `prefer` ditolak pada staging/production. Azure
   menganjurkan `verify-full` kecuali deployment memakai private DNS dengan
   nama berbeda dari hostname sertifikat. Jika `APP_ENV` tidak diset, konfigurasi
   database juga menerapkan kebijakan staging/production; hanya `dev` atau
   `development` yang menggunakan default lokal.
3. Jalankan Alembic sebagai langkah deployment satu kali sebelum backend mulai
   menerima traffic:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
   .\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini current
   .\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini check
   ```

4. Verifikasi `/health/db`, register/login/profile/logout menggunakan akun uji
   khusus environment tersebut, serta pastikan migrasi dan backup berhasil.
   `alembic check` hanya membandingkan metadata model dengan schema yang dapat
   dideteksi autogenerate; itu bukan pengganti penerapan migration dan smoke
   test koneksi pada server Azure yang sebenarnya.
5. Jika ada data yang perlu dipindahkan, rencanakan snapshot konsisten, jeda
   penulisan saat cutover, validasi jumlah/relasi data, dan strategi rollback.
   Jangan melakukan dual-write. Jika database masih kosong, cukup terapkan
   migration dan jalankan smoke test sebelum mengganti traffic.

Gunakan uji Supabase sementara di bagian berikut sebagai rehearsal alur LL-05.
Uji tersebut sengaja meminta URL khusus test dan project reference staging yang
di-allowlist; ia tidak membaca `DATABASE_URL` umum dan menolak target yang
project reference-nya tidak cocok. Cutover Azure memerlukan endpoint dan
kredensial environment yang disediakan pemilik deployment; tidak dijalankan
oleh tahap ini.

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
`python -m alembic -c backend/alembic.ini current` dan diterapkan pada Azure
dengan connection string Azure yang sama-sama PostgreSQL.

Migrasi menyiapkan struktur database. Backend LL-05 kini mengimplementasikan
register/login/logout, hashing password, validasi session, serta GET/PATCH
profile di atas tabel yang sama; tidak diperlukan perubahan skema tambahan
untuk tahap ini. Alur verifikasi identitas tetap di luar implementasi ini:
user baru berstatus `unverified` sampai proses verifikasi terpisah tersedia.

## Verifikasi LL-05 terhadap Supabase sementara

Jalankan test biasa untuk memeriksa endpoint dengan database terisolasi,
kontrak frontend, dan URL PostgreSQL provider-neutral:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
python -m alembic -c backend\alembic.ini upgrade head --sql
```

Perintah Alembic terakhir hanya merender SQL migration tanpa membuka koneksi;
CI menggunakannya sebagai pemeriksaan sintaks/kompatibilitas PostgreSQL umum,
bukan sebagai bukti bahwa server Azure sudah diuji.

Untuk menguji siklus register → login → `/auth/me` → GET/PATCH profile → logout
terhadap database Supabase sementara yang sudah dimigrasikan, simpan
`LL05_TEST_DATABASE_URL` (connection string staging khusus) dan
`LL05_TEST_SUPABASE_PROJECT_REF` (project reference staging yang benar) di
`backend/.env` lokal atau secret environment. Jangan gunakan kredensial
production. Lalu jalankan secara terpisah:

```powershell
$env:LL05_RUN_POSTGRES_INTEGRATION = "1"
try {
    .\.venv\Scripts\python.exe -m pytest backend\tests\test_auth_postgres_integration.py -q
} finally {
    Remove-Item Env:LL05_RUN_POSTGRES_INTEGRATION -ErrorAction SilentlyContinue
}
```

Test berjalan **hanya** jika flag opt-in aktif, URL diberikan melalui variabel
khusus integration test, serta project reference yang diekstrak dari hostname
Supabase langsung atau username shared pooler cocok persis dengan allowlist.
Test membuat dua email acak, memeriksa hash password/session, expiry session,
status identitas awal, duplikasi email, penolakan `user_id` pada PATCH, isolasi
profile, dan logout. Ia memastikan kedua email belum digunakan sebelum menulis,
mencatat hanya primary key dari user yang berhasil dibuat, lalu menghapus
session/profile/user berdasarkan primary key itu di blok `finally`.
