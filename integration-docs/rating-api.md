# Rating API

Konvensi umum (autentikasi, format waktu, format error) ada di [README.md](README.md).

Rating dua arah setelah trip selesai (FR-15): driver memberi rating ke passenger, passenger memberi rating ke driver. Setiap pemberi hanya bisa memberi satu rating ke user yang sama per trip.

Objek **Rating**:

```json
{
  "rating_id": "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d",
  "trip_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
  "rater_id": "a1b2c3d4-0000-4000-8000-000000000002",
  "rated_user_id": "a1b2c3d4-0000-4000-8000-000000000001",
  "role_context": "passenger_to_driver",
  "score": 5
}
```

---

## POST /trips/{trip_id}/ratings

Beri rating. `rater_id` diambil dari token login.

**Body:**

```json
{
  "rated_user_id": "a1b2c3d4-0000-4000-8000-000000000001",
  "role_context": "passenger_to_driver",
  "score": 5
}
```

- `role_context`: `driver_to_passenger` (driver trip → passenger trip) atau `passenger_to_driver` (passenger trip → driver trip). Harus sesuai peran sebenarnya.
- `score`: integer 1–5 (angka, bukan string; desimal ditolak).

Efek samping: rating rata-rata penerima diperbarui otomatis. Rating sebagai driver masuk ke `avg_rating_driver`/`total_ratings_driver` (tampil di `driver` pada `GET /trips/{trip_id}`). Rating sebagai passenger masuk ke `avg_rating`/`total_ratings` user (tampil di `requester` pada `GET /trips/{trip_id}/requests`).

**Response 201:** objek Rating.

**Error:**

| Status | Kapan |
| --- | --- |
| 400 | Merating diri sendiri, atau `role_context` tidak sesuai peran pemberi/penerima di trip ini |
| 403 | Pemberi rating bukan peserta trip (bukan driver dan bukan passenger yang di-accept) |
| 404 | Trip atau user penerima tidak ditemukan |
| 409 | Trip belum `completed`, atau sudah pernah memberi rating ke user ini di trip ini |
| 422 | `score` bukan integer 1–5, `role_context` tidak valid, atau field kurang |

---

## GET /users/{user_id}/ratings

Riwayat rating yang **diterima** user, urut dari trip terbaru.

| Query | Keterangan |
| --- | --- |
| `role_context` | Opsional: `driver_to_passenger` (rating sebagai passenger) atau `passenger_to_driver` (rating sebagai driver) |

**Response 200:**

```json
[
  {
    "rating_id": "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d",
    "trip_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
    "rater_id": "a1b2c3d4-0000-4000-8000-000000000002",
    "rated_user_id": "a1b2c3d4-0000-4000-8000-000000000001",
    "role_context": "passenger_to_driver",
    "score": 5,
    "rater_name": "Sari",
    "trip_departure_time": "2026-10-01T00:30:00Z"
  }
]
```

**Error:**

| Status | Kapan |
| --- | --- |
| 404 | User tidak ditemukan |
| 422 | Nilai `role_context` tidak valid |
