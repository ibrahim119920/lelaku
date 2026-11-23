# Message API

Konvensi umum (autentikasi, format waktu, format error) ada di [README.md](README.md).

Chat per trip (FR-14). Hanya **peserta trip** yang bisa membaca dan mengirim pesan: driver trip dan passenger yang request-nya sudah di-accept (status anggota `active`). Pola akses **polling**, bukan WebSocket.

Objek **Message**:

```json
{
  "message_id": "e1f2a3b4-5c6d-4e7f-8a9b-0c1d2e3f4a5b",
  "trip_id": "5f0c2a8e-6f7b-4c1e-9d55-0b6a4b1d2c3e",
  "sender_id": "a1b2c3d4-0000-4000-8000-000000000002",
  "sender_name": "Sari",
  "content": "Halo pak, saya sudah di gerbang",
  "sent_at": "2026-09-24T10:20:31.123456Z"
}
```

---

## GET /trips/{trip_id}/messages

Riwayat chat, selalu urut dari pesan paling lama ke paling baru.

| Query | Tipe | Keterangan |
| --- | --- | --- |
| `after` | datetime ISO 8601 dengan offset | Opsional. Hanya kembalikan pesan dengan `sent_at` lebih baru dari ini |
| `limit` | int | Default 50, maks 200 |

Cara pakai polling:

1. Saat membuka chat: `GET /trips/{trip_id}/messages` (tanpa `after`) untuk mengambil 50 pesan terbaru.
2. Setiap beberapa detik: `GET /trips/{trip_id}/messages?after=<sent_at pesan terakhir yang dimiliki>`, lalu tambahkan hasilnya ke bawah daftar.

Pakai nilai `sent_at` persis seperti yang dikembalikan server, dan URL-encode (tanda `+` di offset harus menjadi `%2B`; `URLSearchParams` melakukannya otomatis).

**Response 200:** array objek Message.

**Error:**

| Status | Kapan |
| --- | --- |
| 403 | User bukan peserta trip (bukan driver, belum di-accept, atau trip dibatalkan) |
| 404 | Trip tidak ditemukan |
| 422 | `after` bukan datetime dengan offset, atau `limit` di luar rentang |

---

## POST /trips/{trip_id}/messages

Kirim pesan. `sender_id` diambil dari token login.

**Body:**

```json
{ "content": "Halo pak, saya sudah di gerbang" }
```

`content` wajib, 1–2000 karakter.

**Response 201:** objek Message yang baru dibuat.

**Error:**

| Status | Kapan |
| --- | --- |
| 403 | User bukan peserta trip |
| 404 | Trip tidak ditemukan |
| 422 | `content` kosong atau lebih dari 2000 karakter |
