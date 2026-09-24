# Integrasi Backend ↔ Frontend

Dokumentasi kontrak API backend (FastAPI) untuk tim frontend. Satu file per domain:

- [trip-api.md](trip-api.md): publish, search, rekomendasi, detail, status trip, anggota trip
- [riderequest-api.md](riderequest-api.md): permintaan bergabung ke trip
- [message-api.md](message-api.md): chat dalam trip
- [rating-api.md](rating-api.md): rating setelah trip selesai

## Konvensi Umum

- **Base URL (dev):** `http://localhost:8000`. Swagger UI tersedia di `/docs`.
- **Autentikasi:** semua endpoint butuh login. Access token (JWT) dikirim otomatis lewat httpOnly cookie `access_token`, jadi request dari browser wajib memakai `credentials: "include"` (fetch) atau `withCredentials: true` (axios). Untuk testing manual bisa pakai header `Authorization: Bearer <token>`.
- **Format waktu:** ISO 8601 dengan offset zona waktu, mis. `2026-10-01T07:30:00+07:00`. Response dikembalikan dalam UTC (`...Z` / `+00:00`); konversi ke waktu lokal di frontend.
- **Format lokasi:** objek `{ "lat": number, "lng": number }` (hasil geocoding Nominatim).
- **ID:** semua ID berupa UUID string.
- **Format error:** `{ "detail": "Pesan error dalam bahasa Indonesia." }`. Error validasi (422) memakai format bawaan FastAPI: `{ "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }`.

| Status | Arti umum |
| --- | --- |
| 400 | Request valid secara format tapi melanggar aturan bisnis (mis. waktu di masa lalu) |
| 401 | Belum login / token tidak valid atau kedaluwarsa |
| 403 | Login, tapi tidak berhak melakukan aksi ini |
| 404 | Resource tidak ditemukan |
| 409 | Konflik dengan state saat ini (mis. transisi status tidak valid, kursi habis, duplikat) |
| 422 | Body/query tidak sesuai skema (tipe salah, field wajib kosong, di luar rentang) |
