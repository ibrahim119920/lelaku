# Belum Dikerjakan (Backend + Integrasi) — 2026-11-19

Daftar hal yang belum selesai setelah porting auth dari `develop` (async + UUID) dan integrasi frontend dengan API trip. Detail yang sudah dikerjakan ada di `changelogs/backend-changelog.md` dan `changelogs/frontend-changelog.md`.

Prioritas: **P0** memblokir alur utama atau berisiko keamanan, **P1** dibutuhkan sebelum demo, **P2** perbaikan lanjutan.

## 1. Perlu diverifikasi dulu

| Prio | Item | Keterangan |
| --- | --- | --- |
| P0 | Jalankan migration `0006_auth_identity` di database nyata | Baru dicek lewat SQL offline dan test suite (skema dari model). Belum pernah dijalankan lewat Alembic. |
| P0 | Cek isi Supabase | Project kemungkinan paused (`EAUTHQUERY`). Setelah aktif: lihat apakah tabel `users`/`user_sessions` sudah ada dan apa tipe `user_id`-nya. |
| P1 | Hapus container uji | `docker rm -f lelaku-pg-test` setelah Docker Desktop normal. |

Langkah verifikasi migration di database test kosong (pastikan `DATABASE_URL` menunjuk ke `localhost`, jangan ke Supabase):

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_mig alembic upgrade head
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_mig alembic downgrade 0005
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_mig alembic upgrade head
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:55432/lelaku_mig alembic check
```

Kalau tabel versi Text dari develop ternyata sudah ada dan berisi data di Supabase, migration 0006 tidak bisa dipakai apa adanya. Perlu migrasi `user_id` Text ke UUID yang menangani foreign key.

## 2. Fitur backend yang belum ada

| Prio | Item | Dampak |
| --- | --- | --- |
| P0 | Cara menjadi driver terverifikasi | Belum ada endpoint yang membuat `driver_profiles` atau mengubah `verification_status`. Akibatnya `POST /trips` selalu 403 untuk user nyata (hanya jalan di test lewat data seed). |
| P0 | Modul kendaraan (`vehicles`) | Belum ada endpoint tambah/lihat kendaraan. `Vehicle` masih placeholder, dan form buat trip meminta UUID kendaraan manual. |
| P1 | Upload dokumen identitas (FR-03) | Hanya kolom `identity_status` dan `document_url` yang ada. Belum ada upload, penyimpanan file, atau alur verifikasi. |
| P1 | Daftar request milik passenger | Passenger belum bisa melihat request `pending` miliknya (butuh mis. `GET /requests/me`). |
| P1 | Modul risk (FR-08) | Belum dirancang endpoint dan integrasinya. Menunggu keputusan konsep ML. |
| P2 | Pembersihan sesi kedaluwarsa | Baris `user_sessions` yang kedaluwarsa/dicabut menumpuk. Perlu job berkala. |
| P2 | Tabel `trip_matches` | Dipertahankan di skema tapi tidak diisi (keputusan MVP). |

## 3. Keamanan

| Prio | Item | Keterangan |
| --- | --- | --- |
| P0 | Naikkan `next` dari `15.2.0` | Versi yang dikunci develop ditandai npm rentan (CVE-2025-66478). Perlu keputusan tim karena pin berasal dari teman. Cek juga versi `react`. |
| P1 | Rate limiting login dan register | Belum ada. Brute force password dan banjir hashing Argon2 masih mungkin. |
| P1 | Pastikan `APP_ENV` di production bukan `development` | Nilai `development` mematikan flag `Secure` pada cookie sesi. |
| P2 | Tinjau ulang CORS dan CSRF sebelum deploy | Saat ini mengandalkan `SameSite=Lax` dan daftar origin yang ketat. Jangan dilonggarkan. |

## 4. Frontend

| Prio | Item | Keterangan |
| --- | --- | --- |
| P1 | Pakai `/auth/me` untuk identitas user | Sekarang peran driver disimpulkan dari `GET /trips/{id}/requests` (403 = bukan driver). Dengan `user_id` dari `/auth/me`, tebakan ini bisa dihapus dan chat bisa membedakan pesan sendiri. |
| P1 | Pilihan kendaraan di form buat trip | Menunggu modul kendaraan. |
| P1 | Halaman profil menampilkan rating dan riwayat | Profil dari develop baru memuat data akun dasar. |
| P2 | Gabungkan dua klien API | `lib/api/client.ts` (trip) dan `lib/auth/client.ts` (auth) menduplikasi logika fetch dan error. |
| P2 | Hapus stub `app/api/{trips,messages,join-requests}/route.ts` | Tidak dipakai lagi. |
| P2 | Peta (Leaflet/OSM) dan reverse geocoding | Kartu trip masih menampilkan koordinat, bukan nama tempat. |
| P2 | Test frontend untuk view baru | Baru ada 8 unit test auth dari develop. |
| P2 | Teks placeholder di halaman utama | Kartu "Mulai dari sini" masih berisi catatan scaffold. |

## 5. Infrastruktur, dokumentasi, dan merge

| Prio | Item | Keterangan |
| --- | --- | --- |
| P0 | Rencanakan merge dengan `develop` | Akan konflik di `backend/app/main.py`, `backend/app/models.py`, `backend/requirements*.txt`, `backend/.env.example`, dan `frontend/*`. Develop memakai file datar `backend/app/*.py` dengan import `backend.app.*` dan folder `backend/migrations/`. Versi kita memakai `backend/app/<modul>/` dan `backend/alembic/`. Perlu disepakati dengan pemilik kode auth sebelum merge. |
| P1 | CI hanya markdown lint | Tambah job `pytest` (dengan service Postgres), `tsc --noEmit`, `vitest`, dan `next build`. |
| P1 | `docs/` dari develop belum dibawa | `docs/database-setup.md` dan `docs/dokumentasi-proyek.md` menggambarkan setup sync/psycopg, jadi perlu disesuaikan dulu. `docs/auth-profile-contract.md` perlu catatan deviasi. |
| P2 | Deviasi dari kontrak LL-05 | `user_id` UUID (kontrak: contoh string), `avg_rating` bernilai `0.0` saat belum ada rating (kontrak: `null`), email output bertipe `str`. Perlu disepakati atau didokumentasikan. |
| P2 | Nama folder tidak sesuai `CLAUDE.md` | Dokumen menyebut `integration/` dan `ml/`, repo memakai `integration-docs/` dan belum punya `ml/`. |
| P2 | `.vs/` ikut ter-track di git | Cache Visual Studio sebaiknya dikeluarkan dari repo. |
