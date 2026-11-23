# Trip API

Konvensi umum (autentikasi, format waktu/lokasi, format error) ada di [README.md](README.md).

Objek **Trip** yang dipakai di banyak response:

```json
{
  "trip_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
  "driver_id": "a1b2c3d4-0000-4000-8000-000000000001",
  "vehicle_id": "a1b2c3d4-0000-4000-8000-0000000000v1",
  "origin": { "lat": -7.7713, "lng": 110.3776 },
  "destination": { "lat": -7.7925, "lng": 110.3658 },
  "departure_time": "2026-10-01T00:30:00Z",
  "available_seats": 3,
  "status": "published",
  "estimated_total_cost": 45000.0,
  "cost_per_seat": 15000.0
}
```

`status` salah satu dari `published`, `ongoing`, `completed`, `cancelled`.

---

## POST /trips

Driver mempublikasikan trip baru (FR-11).

**Body:**

```json
{
  "vehicle_id": "a1b2c3d4-0000-4000-8000-0000000000v1",
  "origin": { "lat": -7.7713, "lng": 110.3776 },
  "destination": { "lat": -7.7925, "lng": 110.3658 },
  "departure_time": "2026-10-01T07:30:00+07:00",
  "available_seats": 3,
  "cost_per_seat": 15000
}
```

- `departure_time` wajib menyertakan offset zona waktu dan harus di masa depan.
- `available_seats` minimal 1 dan tidak boleh melebihi `capacity` kendaraan.
- `cost_per_seat` ≥ 0. `estimated_total_cost` dihitung server (`cost_per_seat × available_seats`).

**Response 201:** objek Trip dengan `status: "published"`.

**Error:**

| Status | Kapan |
| --- | --- |
| 400 | `available_seats` melebihi kapasitas kendaraan, atau `departure_time` tidak di masa depan |
| 403 | User bukan driver terverifikasi (`verification_status` ≠ `verified`), atau kendaraan bukan miliknya |
| 404 | `vehicle_id` tidak ditemukan |
| 422 | Field kurang/tipe salah, lat/lng di luar rentang, `departure_time` tanpa offset |

---

## GET /trips

Cari trip berstatus `published` (FR-06). Semua query parameter opsional.

| Query | Tipe | Keterangan |
| --- | --- | --- |
| `origin_lat`, `origin_lng` | number | Harus diisi berpasangan. Cocok kalau origin trip ≤ 2 km dari titik ini |
| `destination_lat`, `destination_lng` | number | Harus diisi berpasangan. Cocok kalau destination trip ≤ 2 km |
| `date` | `YYYY-MM-DD` | Tanggal keberangkatan, ditafsirkan dalam zona WIB (`Asia/Jakarta`) |
| `time` | `HH:MM` | Wajib disertai `date`. Cocok kalau keberangkatan dalam ±2 jam dari waktu ini |
| `limit` | int | Default 50, maks 100 |
| `offset` | int | Default 0 |

Contoh: `GET /trips?origin_lat=-7.778&origin_lng=110.38&destination_lat=-7.799&destination_lng=110.365&date=2026-10-01&time=07:00`

**Response 200:** array objek Trip, urut `departure_time` paling awal.

**Error:**

| Status | Kapan |
| --- | --- |
| 400 | Hanya salah satu dari `*_lat`/`*_lng` yang diisi, atau `time` tanpa `date` |
| 422 | Format angka/tanggal/jam salah, atau di luar rentang |

---

## GET /trips/recommended?trip_id={trip_id}

Rekomendasi trip yang mirip dengan trip acuan (FR-07). Dihitung real-time: origin dan destination masing-masing ≤ 2 km (Haversine), selisih `departure_time` ≤ 2 jam, hanya trip `published`. Trip acuan sendiri dan trip milik user yang request tidak ikut. Urut `score` tertinggi.

`score` bernilai 0–1 (1 = origin, destination, dan waktu identik), rata-rata dari tiga komponen dengan bobot sama.

**Response 200:**

```json
[
  {
    "trip": { "trip_id": "…", "origin": { "lat": -7.778, "lng": 110.38 }, "…": "objek Trip lengkap" },
    "origin_distance_km": 0.779,
    "destination_distance_km": 0.724,
    "time_diff_minutes": 30.0,
    "score": 0.6106
  }
]
```

**Error:**

| Status | Kapan |
| --- | --- |
| 404 | `trip_id` acuan tidak ditemukan |
| 422 | `trip_id` tidak ada atau bukan UUID |

---

## GET /trips/{trip_id}

Detail trip (FR-09), termasuk info driver dan kendaraan.

**Response 200:** objek Trip ditambah:

```json
{
  "…": "semua field objek Trip",
  "driver": {
    "user_id": "a1b2c3d4-0000-4000-8000-000000000001",
    "name": "Budi",
    "profile_photo": null,
    "avg_rating_driver": 4.5,
    "total_ratings_driver": 12
  },
  "vehicle": {
    "vehicle_id": "a1b2c3d4-0000-4000-8000-0000000000v1",
    "type": "car",
    "brand": "Toyota",
    "model": "Avanza",
    "plate_number": "AB 1234 XY",
    "capacity": 4
  }
}
```

**Error:** 404 kalau trip tidak ditemukan.

---

## GET /trips/me/published

Semua trip yang dipublikasikan user login sebagai driver (semua status), urut `departure_time` terbaru.

**Response 200:** array objek Trip.

---

## GET /trips/me/joined

Semua trip yang diikuti user login sebagai passenger (FR-13): trip yang akan datang dan riwayat, semua status. Urut `departure_time` terbaru.

**Response 200:** array objek Trip ditambah `member_status`:

```json
[
  {
    "…": "semua field objek Trip",
    "status": "completed",
    "member_status": "active"
  }
]
```

`member_status` bernilai `active`, atau `cancelled` kalau trip dibatalkan driver.

---

## GET /trips/{trip_id}/members

Daftar anggota trip: driver (selalu elemen pertama) diikuti passenger yang request-nya diterima. Read-only; anggota terbentuk otomatis saat driver menerima request (lihat [riderequest-api.md](riderequest-api.md)).

**Response 200:**

```json
[
  {
    "user_id": "a1b2c3d4-0000-4000-8000-000000000001",
    "name": "Budi",
    "profile_photo": null,
    "role": "driver",
    "trip_member_id": null,
    "status": "active"
  },
  {
    "user_id": "a1b2c3d4-0000-4000-8000-000000000002",
    "name": "Sari",
    "profile_photo": null,
    "role": "passenger",
    "trip_member_id": "c7d8e9f0-1a2b-4c3d-8e4f-5a6b7c8d9e0f",
    "status": "active"
  }
]
```

`trip_member_id` selalu `null` untuk driver karena driver tidak disimpan sebagai baris Tripmember.

**Error:** 404 kalau trip tidak ditemukan.

---

## PATCH /trips/{trip_id}/status

Driver mengubah status trip secara manual.

**Body:**

```json
{ "status": "ongoing" }
```

`status` salah satu dari `ongoing`, `completed`, `cancelled`. Transisi yang diizinkan:

| Dari | Ke |
| --- | --- |
| `published` | `ongoing`, `cancelled` |
| `ongoing` | `completed`, `cancelled` |
| `completed`, `cancelled` | (final, tidak bisa diubah) |

Efek `cancelled`: semua passenger di trip ini `member_status`-nya menjadi `cancelled` (akses chat passenger tertutup).

**Response 200:** objek Trip dengan status baru.

**Error:**

| Status | Kapan |
| --- | --- |
| 403 | User bukan driver pemilik trip |
| 404 | Trip tidak ditemukan |
| 409 | Transisi tidak diizinkan (lompat, mundur, atau status sama) |
| 422 | `status` bukan salah satu dari tiga nilai di atas |
