# Kontrak implementasi Auth dan Profile (LL-05)

Kontrak ini merinci DTO dan endpoint LL-05. Penambahan schema `identity_status`
dan `USER_SESSION` telah disetujui Bayu. Jika kontrak endpoint LL-03 berbeda,
kontrak utama LL-03 tetap menjadi acuan.

## Batas data

Endpoint auth/profile hanya mengembalikan DTO publik berikut:

```json
{
  "user_id": "user-123",
  "name": "Nama Pengguna",
  "email": "user@example.com",
  "phone": "+628123456789",
  "profile_photo": null,
  "identity_status": "unverified",
  "avg_rating": null,
  "total_ratings": 0,
  "total_trips_completed": 0
}
```

`password_hash` tidak boleh ada di DTO, response, log request, atau payload
client. DTO profile selalu merepresentasikan pengguna dari session aktif; tidak
ada `user_id` dari client yang dipakai untuk memilih target profile.

## Penyesuaian schema LL-05 yang disetujui

Bayu menyetujui penyesuaian schema berikut untuk mendukung LL-05:

- Tambahkan `USER.identity_status`, dengan nilai yang diizinkan `verified` dan
  `unverified`.
- Nilai awal user baru adalah `unverified`.
- Pertahankan `DRIVER_PROFILE.verification_status` sebagai status verifikasi
  khusus driver; field ini bukan pengganti `USER.identity_status`.
- Tambahkan `USER_SESSION` untuk session server-side. Simpan digest SHA-256 dari
  token opaque, bukan token cookie mentah; catat pemilik, waktu pembuatan,
  kedaluwarsa, dan pencabutan session.

Implementasi fisik memakai nama tabel PostgreSQL `users`, `driver_profiles`,
dan `user_sessions`.

## Session

Backend membuat session server-side setelah login dan mengirim cookie:

```text
Set-Cookie: lelaku_session=<opaque-session-id>; HttpOnly; Secure; SameSite=Lax; Path=/
```

Session ID harus opaque dan tidak memuat password atau data sensitif. Browser
mengirim cookie dengan `credentials: include`. Frontend tidak menyimpan token
atau session ID di `localStorage`, `sessionStorage`, query string, atau cookie
yang dapat dibaca JavaScript. Logout membatalkan session di backend dan
menghapus cookie dengan atribut yang sama.

Browser memanggil FastAPI langsung. CORS hanya mengizinkan origin persis dari
`NEXT_PUBLIC_APP_URL` dan memakai `credentials: include`; wildcard origin tidak
digunakan. Cookie tidak menetapkan `Domain`, sehingga bersifat host-only.
`SameSite=Lax`; `Secure` aktif otomatis ketika `APP_ENV=production` dan hanya
nonaktif pada development HTTP lokal. TTL default tujuh hari dan dapat diatur
melalui `SESSION_TTL_SECONDS` (maksimum 30 hari).

Pada deployment, Next.js server-side auth perlu menerima cookie yang sama.
Karena itu frontend dan backend harus berbagi host cookie, misalnya dengan
reverse proxy/BFF pada origin yang sama atau domain cookie bersama yang telah
disetujui. Jangan mengandalkan cookie host-only lintas subdomain.

## Endpoint

Semua response JSON sukses menggunakan envelope `{ "data": ... }`. Bila
endpoint mengembalikan user, `data` berisi DTO publik di atas atau object
`{ "user": <DTO publik> }`.

### `POST /auth/register`

Request:

```json
{
  "name": "Nama Pengguna",
  "email": "user@example.com",
  "phone": "+628123456789",
  "password": "minimum-8-characters"
}
```

Response `201` mengembalikan `{"data": <DTO user publik>}`. FastAPI memvalidasi
input, memangkas dan menormalisasi email ke huruf kecil, menolak email duplikat,
dan menyimpan password hanya sebagai hash Argon2. Email duplikat menghasilkan
`409` dengan kode `EMAIL_ALREADY_EXISTS`.

### `POST /auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "minimum-8-characters"
}
```

Response `200` mengembalikan `{"data": <DTO user publik>}` dan mengatur cookie
session. Kredensial salah menghasilkan respons yang sama (`401`, `AUTH_INVALID`)
tanpa membedakan email tidak terdaftar dan password salah.

### `POST /auth/logout`

Response `204` tanpa body. Backend membatalkan session aktif dan menghapus
cookie session. Request tanpa session boleh tetap menghasilkan `204` agar
logout idempotent.

### `GET /auth/me`

Response `200` mengembalikan user publik dari session aktif. Tanpa session atau
session tidak valid, response adalah `401` dengan error `AUTH_UNAUTHENTICATED`.

### `GET /profile`

Response `200` mengembalikan user publik dari session aktif. Tanpa session,
response adalah `401`.

### `PATCH /profile`

Request hanya mengizinkan field berikut:

```json
{
  "name": "Nama Baru",
  "phone": "+628123456789"
}
```

`email`, `password_hash`, `identity_status`, rating, dan agregat perjalanan
tidak boleh diubah melalui endpoint ini. Response `200` mengembalikan DTO
profile terbaru. Tanpa session, response `401`; input tidak valid memakai
`422`.

## Bentuk error minimum

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Periksa kembali input.",
    "fields": {
      "email": "Format email tidak valid."
    }
  }
}
```

`fields` boleh tidak ada untuk error non-form. `message` harus aman ditampilkan
ke pengguna dan tidak boleh berisi password, hash, session ID, atau detail SQL.

## Status implementasi

Register dan login FastAPI mengikuti kontrak di atas. Logout, pemeriksaan
session (`/auth/me`), proteksi endpoint, serta GET/PATCH profile masih menunggu
tahap implementasi berikutnya. Frontend di branch LL-05 memanggil API melalui
`NEXT_PUBLIC_API_BASE_URL`; server component memakai `BACKEND_API_URL`.
