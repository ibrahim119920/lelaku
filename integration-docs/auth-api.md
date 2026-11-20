# Auth & Profile API

Konvensi umum ada di [README.md](README.md). Modul ini memakai format error sendiri (`{"error": {...}}`), berbeda dari endpoint trip/chat (`{"detail": ...}`); lihat bagian [Format error](#format-error).

## Sesi

Login membuat **sesi server-side**. Backend mengirim cookie opaque dan hanya menyimpan hash SHA-256-nya di database:

```text
Set-Cookie: lelaku_session=<token>; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800
```

- `Secure` aktif untuk semua nilai `APP_ENV` selain `dev`/`development` (production wajib HTTPS).
- Browser mengirim cookie otomatis; request dari frontend wajib memakai `credentials: "include"`.
- Frontend **tidak boleh** menyimpan token di `localStorage`/`sessionStorage`/query string; cookie `HttpOnly` memang tidak terbaca JavaScript.
- Masa berlaku default 7 hari (`SESSION_TTL_SECONDS`). Logout mencabut sesi di server.
- Cookie ini juga yang mengautentikasi **semua endpoint lain** (trip, request, chat, rating). Header `Authorization: Bearer` tidak lagi dikenali.
- Server component Next.js harus meneruskan cookie `lelaku_session` ke backend (`BACKEND_API_URL`); lihat `frontend/src/lib/server/auth.ts`.

Objek **User** (DTO publik, tidak pernah memuat `password_hash`):

```json
{
  "user_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
  "name": "Naya Pengguna",
  "email": "naya@example.com",
  "phone": "+628123456789",
  "profile_photo": null,
  "identity_status": "unverified",
  "avg_rating": 0.0,
  "total_ratings": 0,
  "total_trips_completed": 0
}
```

`identity_status` salah satu dari `verified`, `unverified` (akun baru selalu `unverified`). `user_id` berupa UUID. `avg_rating` bernilai `0.0` selama belum ada rating.

Semua response sukses berbentuk `{ "data": <User> }` dan memakai `Cache-Control: no-store`.

---

## POST /auth/register

Daftar akun baru (FR-01).

**Body:**

```json
{
  "name": "Naya Pengguna",
  "email": "Naya@Example.com",
  "phone": "+62 812-3456-789",
  "password": "minimal-8-karakter"
}
```

- `name` 2–200 karakter, `phone` 7–15 digit (boleh diawali `+`, spasi/titik/strip/kurung), `password` 8–128 karakter.
- `email` dinormalisasi ke huruf kecil; keunikan dicek tanpa membedakan huruf besar/kecil.
- Field lain (mis. `identity_status`) ditolak 422.
- Register **tidak** otomatis login; panggil `POST /auth/login` setelahnya.

**Response 201:** `{ "data": <User> }`

**Error:**

| Status | Kode | Kapan |
| --- | --- | --- |
| 409 | `EMAIL_ALREADY_EXISTS` | Email sudah terdaftar |
| 422 | `VALIDATION_ERROR` | Input tidak valid; lihat `error.fields` |

---

## POST /auth/login

Login dan mulai sesi (FR-02).

**Body:**

```json
{ "email": "naya@example.com", "password": "minimal-8-karakter" }
```

**Response 200:** `{ "data": <User> }` plus `Set-Cookie: lelaku_session=...`. Tiap login membuat sesi baru yang independen.

**Error:**

| Status | Kode | Kapan |
| --- | --- | --- |
| 401 | `AUTH_INVALID` | Email tidak terdaftar **atau** password salah (respons sengaja identik) |
| 422 | `VALIDATION_ERROR` | Email/password kosong atau format salah |

---

## POST /auth/logout

Cabut sesi aktif dan hapus cookie (FR-02).

**Response 204** tanpa body. Idempotent: tanpa cookie atau dengan sesi yang sudah mati tetap `204`.

---

## GET /auth/me

User dari sesi aktif. Dipakai frontend untuk guard halaman.

**Response 200:** `{ "data": <User> }`

**Error:** 401 `AUTH_UNAUTHENTICATED` kalau tidak ada sesi, sesi kedaluwarsa, atau sudah dicabut.

---

## GET /profile

Sama dengan `GET /auth/me`; profil selalu milik user dari sesi (tidak ada `user_id` dari client).

---

## PATCH /profile

Ubah profil sendiri (FR-05).

**Body:**

```json
{ "name": "Nama Baru", "phone": "+628123456789" }
```

Hanya `name` dan `phone`. Field lain (`email`, `identity_status`, rating, dst.) ditolak 422.

**Response 200:** `{ "data": <User> }` terbaru.

**Error:**

| Status | Kode | Kapan |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHENTICATED` | Tidak ada sesi valid |
| 422 | `VALIDATION_ERROR` | Input tidak valid |

---

## Format error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Periksa kembali input.",
    "fields": { "email": "Masukkan email yang valid." }
  }
}
```

`fields` hanya ada untuk error validasi form. `message` aman ditampilkan ke pengguna.

Kode `503 SERVICE_UNAVAILABLE` (`"Layanan sementara tidak tersedia. Coba lagi nanti."`) dikembalikan semua endpoint kalau database tidak terjangkau. Frontend sebaiknya membedakannya dari 401: **jangan** menganggap 503 sebagai logout.

Endpoint trip/chat/rating yang dipanggil tanpa sesi valid juga membalas `401` dengan format `{"error": {"code": "AUTH_UNAUTHENTICATED", ...}}` (bukan `{"detail": ...}`).
