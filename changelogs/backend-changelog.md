# Backend Changelog

Semua perubahan penting pada backend (FastAPI) dicatat di file ini.

## [2026-09-24] Scaffold backend FastAPI + placeholder modul auth

**Jenis:** Fitur baru
**Deskripsi:** Membuat fondasi backend karena `backend/` masih kosong: struktur layered (`app/core`, `app/trip`, `app/chat`), SQLAlchemy async + asyncpg, Alembic mode async (`run_sync`), error domain (`AppError` → 400/403/404/409), CORS dengan credentials, dan dependency `get_current_user_id` yang membaca JWT dari httpOnly cookie `access_token` (fallback header `Authorization: Bearer`). Modul auth asli dikerjakan anggota tim lain dan belum masuk repo, jadi model `users`, `driver_profiles`, `vehicles`, `user_sessions` (sesuai ERD) dibuat sebagai **placeholder** di `app/auth/models.py` + migration `0001_auth_placeholder`, ditandai `TODO(auth)`. Saat kode auth asli masuk: hapus placeholder tersebut, ganti `get_current_user_id`, dan arahkan `down_revision` migration `0002_trip` ke revision terakhir modul auth.
**File yang terdampak:** backend/app/main.py, backend/app/core/config.py, backend/app/core/database.py, backend/app/core/security.py, backend/app/core/deps.py, backend/app/core/exceptions.py, backend/app/auth/models.py, backend/app/models.py, backend/alembic.ini, backend/alembic/env.py, backend/alembic/script.py.mako, backend/alembic/versions/0001_auth_placeholder.py, backend/requirements.txt, backend/requirements-dev.txt, backend/.env.example, backend/pytest.ini, backend/tests/conftest.py

## [2026-09-24] Domain Trip: publish, search, rekomendasi, detail, status

**Jenis:** Fitur baru
**Deskripsi:** Menambahkan tabel `trips` (status enum `trip_status`: published/ongoing/completed/cancelled, lokasi sebagai 4 kolom lat/lng) dan `trip_matches` (sesuai ERD, sengaja tidak diisi). Endpoint: `POST /trips` (hanya driver `verified`, kendaraan milik sendiri, `available_seats` ≤ kapasitas kendaraan, `departure_time` di masa depan; server menghitung `estimated_total_cost = cost_per_seat × available_seats`), `GET /trips` (search FR-06: radius 2 km untuk origin/destination, `date`/`time` ditafsirkan di zona `APP_TIMEZONE` dengan toleransi ±2 jam), `GET /trips/recommended` (FR-07, Haversine on-the-fly: origin & destination ≤ 2 km, selisih waktu ≤ 2 jam, skor 0–1 bobot sama, trip milik user sendiri tidak ikut), `GET /trips/{trip_id}` (FR-09, plus info driver & kendaraan), `GET /trips/me/published`, dan `PATCH /trips/{trip_id}/status` (hanya driver pemilik; transisi published→ongoing/cancelled, ongoing→completed/cancelled). Threshold matching ada di `app/trip/matching.py`. `GET /trips/me/joined` menyusul di entry Tripmember karena bergantung pada tabel `trip_members`.
**File yang terdampak:** backend/app/trip/models.py, backend/app/trip/matching.py, backend/app/trip/schemas.py, backend/app/trip/repository.py, backend/app/trip/service.py, backend/app/trip/router.py, backend/alembic/versions/0002_trip.py, backend/tests/test_trips.py, backend/tests/test_matching.py

## [2026-09-24] Domain Riderequest: ajukan, lihat, accept/reject request

**Jenis:** Fitur baru
**Deskripsi:** Menambahkan tabel `ride_requests` (status `pending`/`accepted`/`rejected`, `pickup` string bebas ≤ 255 karakter) dan endpoint `POST /trips/{trip_id}/requests` (FR-10), `GET /trips/{trip_id}/requests` (FR-12, hanya driver pemilik, filter opsional `?status=`), serta `PATCH /trips/{trip_id}/requests/{request_id}` (accept/reject). Aturan: request hanya ke trip `published` yang masih punya kursi; driver tidak bisa request ke trip sendiri; satu request `pending`/`accepted` per passenger per trip (409; boleh request ulang setelah `rejected`), dijaga juga oleh partial unique index `uq_ride_requests_active_per_requester`. Accept hanya selama trip `published`, ditolak 409 kalau `available_seats` = 0; baris trip dikunci (`SELECT … FOR UPDATE`) supaya accept bersamaan tidak membuat kursi negatif (ditambah check constraint `available_seats >= 0`). Request yang sudah diproses tidak bisa diubah lagi (409).
**File yang terdampak:** backend/app/trip/models.py, backend/app/trip/schemas.py, backend/app/trip/repository.py, backend/app/trip/service.py, backend/app/trip/router.py, backend/alembic/versions/0003_riderequest_tripmember.py, backend/tests/test_riderequests.py

## [2026-09-24] Domain Tripmember: auto-create saat accept, daftar anggota, trip yang diikuti

**Jenis:** Fitur baru
**Deskripsi:** Menambahkan tabel `trip_members` (status `active`/`cancelled`, satu baris per passenger per trip, `ride_request_id` unik). Baris dibuat otomatis saat request di-accept, tidak ada endpoint create manual. Driver **tidak** disimpan sebagai baris Tripmember; dia anggota implisit lewat `trips.driver_id` (keputusan tim). Endpoint baru: `GET /trips/{trip_id}/members` (driver + passenger) dan `GET /trips/me/joined` (FR-13, semua trip yang diikuti sebagai passenger beserta `member_status`). Saat trip di-`cancelled`, semua Tripmember `active` di trip itu ikut jadi `cancelled`. Tabel `ride_requests` dan `trip_members` ada di satu migration karena accept langsung membutuhkan keduanya.
**File yang terdampak:** backend/app/trip/models.py, backend/app/trip/schemas.py, backend/app/trip/repository.py, backend/app/trip/service.py, backend/app/trip/router.py, backend/alembic/versions/0003_riderequest_tripmember.py, backend/tests/test_riderequests.py

## [2026-09-24] Domain Message: chat dalam trip (polling)

**Jenis:** Fitur baru
**Deskripsi:** Menambahkan modul `app/chat` dengan tabel `messages` (index `trip_id, sent_at`) dan endpoint `GET /trips/{trip_id}/messages` serta `POST /trips/{trip_id}/messages` (FR-14). Akses hanya untuk driver trip dan passenger dengan Tripmember `active`; request yang masih pending, user luar, dan passenger dari trip yang dibatalkan mendapat 403. `sender_id` diambil dari token. Pola polling: tanpa parameter mengembalikan `limit` pesan terbaru (default 50, maks 200); dengan `?after=<sent_at terakhir>` hanya pesan yang lebih baru. Keduanya urut dari yang paling lama. `content` 1–2000 karakter.
**File yang terdampak:** backend/app/chat/models.py, backend/app/chat/schemas.py, backend/app/chat/repository.py, backend/app/chat/service.py, backend/app/chat/router.py, backend/app/main.py, backend/app/models.py, backend/alembic/versions/0004_message.py, backend/tests/test_messages.py, backend/tests/conftest.py

## [2026-09-24] Domain Rating: rating dua arah setelah trip selesai

**Jenis:** Fitur baru
**Deskripsi:** Menambahkan tabel `ratings` dengan constraint database `score BETWEEN 1 AND 5`, `role_context` valid, `rater_id <> rated_user_id`, dan unik per `(trip_id, rater_id, rated_user_id)`. Endpoint `POST /trips/{trip_id}/ratings` (FR-15) dan `GET /users/{user_id}/ratings` (filter opsional `?role_context=`). Aturan: trip harus `completed` (409), pemberi rating harus peserta trip (403), `role_context` harus sesuai peran sebenarnya: `driver_to_passenger` hanya driver → passenger trip itu, `passenger_to_driver` hanya passenger → driver trip itu (400), duplikat ditolak 409, `score` wajib integer 1–5 (Pydantic strict, 422). Efek samping di service layer: agregat dihitung ulang dari tabel `ratings` dan **dipisah per peran**: `driver_to_passenger` memperbarui `users.avg_rating`/`total_ratings` (rating sebagai passenger), sedangkan `passenger_to_driver` memperbarui `driver_profiles.avg_rating_driver`/`total_ratings_driver`. Baris user penerima dikunci supaya rating bersamaan tidak saling menimpa agregat.
**File yang terdampak:** backend/app/trip/models.py, backend/app/trip/schemas.py, backend/app/trip/repository.py, backend/app/trip/service.py, backend/app/trip/router.py, backend/app/main.py, backend/app/models.py, backend/alembic/versions/0005_rating.py, backend/tests/test_ratings.py
