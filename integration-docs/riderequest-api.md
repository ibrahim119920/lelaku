# Riderequest API

Konvensi umum (autentikasi, format waktu, format error) ada di [README.md](README.md).

Alur: passenger mengajukan request ke trip `published` → driver melihat daftar request → driver accept/reject. Kalau di-accept, passenger otomatis menjadi anggota trip (lihat `GET /trips/{trip_id}/members` di [trip-api.md](trip-api.md)) dan `available_seats` trip berkurang 1.

Objek **RideRequest**:

```json
{
  "request_id": "9d3e1c7a-2b4f-4a8e-8c1d-5e6f7a8b9c0d",
  "trip_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
  "requester_id": "a1b2c3d4-0000-4000-8000-000000000002",
  "pickup": "Gerbang utama UGM",
  "status": "pending",
  "created_at": "2026-09-24T10:15:00Z"
}
```

`status` salah satu dari `pending`, `accepted`, `rejected`.

---

## POST /trips/{trip_id}/requests

Passenger mengajukan permintaan bergabung (FR-10).

**Body:**

```json
{ "pickup": "Gerbang utama UGM" }
```

`pickup` wajib, string 1–255 karakter (alamat bebas atau `"lat,lng"`).

**Response 201:** objek RideRequest dengan `status: "pending"`.

**Error:**

| Status | Kapan |
| --- | --- |
| 403 | User adalah driver trip ini |
| 404 | Trip tidak ditemukan |
| 409 | Trip tidak berstatus `published`, kursi sudah penuh, atau user sudah punya request `pending`/`accepted` di trip ini. Request baru boleh diajukan lagi kalau request sebelumnya `rejected` |
| 422 | `pickup` kosong atau lebih dari 255 karakter |

---

## GET /trips/{trip_id}/requests

Driver melihat daftar request masuk (FR-12), urut dari yang paling lama.

| Query | Keterangan |
| --- | --- |
| `status` | Opsional: `pending`, `accepted`, atau `rejected` |

**Response 200:**

```json
[
  {
    "request_id": "9d3e1c7a-2b4f-4a8e-8c1d-5e6f7a8b9c0d",
    "trip_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
    "requester_id": "a1b2c3d4-0000-4000-8000-000000000002",
    "pickup": "Gerbang utama UGM",
    "status": "pending",
    "created_at": "2026-09-24T10:15:00Z",
    "requester": {
      "user_id": "a1b2c3d4-0000-4000-8000-000000000002",
      "name": "Sari",
      "profile_photo": null,
      "avg_rating": 4.8,
      "total_ratings": 5
    }
  }
]
```

**Error:**

| Status | Kapan |
| --- | --- |
| 403 | User bukan driver pemilik trip |
| 404 | Trip tidak ditemukan |
| 422 | Nilai `status` tidak valid |

---

## PATCH /trips/{trip_id}/requests/{request_id}

Driver menerima atau menolak request.

**Body:**

```json
{ "status": "accepted" }
```

`status` salah satu dari `accepted`, `rejected`.

Efek `accepted`: baris Tripmember dibuat otomatis dan `available_seats` trip berkurang 1.

**Response 200:** objek RideRequest dengan status baru.

**Error:**

| Status | Kapan |
| --- | --- |
| 403 | User bukan driver pemilik trip |
| 404 | Trip tidak ditemukan, atau request tidak ada di trip ini |
| 409 | Request sudah diproses sebelumnya; atau (khusus `accepted`) trip tidak lagi `published` atau `available_seats` sudah 0 |
| 422 | `status` bukan `accepted`/`rejected` |
