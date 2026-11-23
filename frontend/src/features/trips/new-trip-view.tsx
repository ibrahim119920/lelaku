"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ErrorNotice } from "@/components/ui/error-notice";
import { ApiError, apiFetch, jsonBody, toApiError } from "@/lib/api/client";
import { geocode } from "@/lib/api/geocode";
import type { Trip } from "@/lib/api/types";

export default function NewTripView() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<ApiError | string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSubmitting(true);
    setError(null);

    try {
      // Sengaja berurutan: Nominatim membatasi 1 request/detik.
      const origin = await geocode(String(form.get("origin")).trim());
      const destination = await geocode(String(form.get("destination")).trim());

      const trip = await apiFetch<Trip>(
        "/trips",
        jsonBody({
          vehicle_id: String(form.get("vehicle_id")).trim(),
          origin,
          destination,
          // datetime-local tanpa zona; new Date() menafsirkannya di zona browser,
          // toISOString() menghasilkan offset "Z" yang diwajibkan backend.
          departure_time: new Date(String(form.get("departure"))).toISOString(),
          available_seats: Number(form.get("available_seats")),
          cost_per_seat: Number(form.get("cost_per_seat")),
        }),
      );
      router.push(`/trips/${trip.trip_id}`);
    } catch (err) {
      // ApiError dari backend, atau Error biasa dari geocoding (pesan sudah ramah pengguna).
      setError(err instanceof ApiError ? err : err instanceof Error ? err.message : toApiError(err));
      setSubmitting(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="card">
        <p>
          <Link className="text-link" href="/trips">
            ← Kembali ke perjalanan
          </Link>
        </p>
        <h1>Buat perjalanan</h1>
        <p className="muted">
          Bagikan rencana perjalananmu dengan calon teman seperjalanan. Hanya driver
          terverifikasi yang bisa mempublikasikan perjalanan.
        </p>

        <form className="form-grid" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="origin">Titik keberangkatan</label>
            <input id="origin" name="origin" type="text" required />
          </div>
          <div className="field">
            <label htmlFor="destination">Tujuan</label>
            <input id="destination" name="destination" type="text" required />
          </div>
          <div className="field">
            <label htmlFor="departure">Waktu keberangkatan</label>
            <input id="departure" name="departure" type="datetime-local" required />
          </div>
          <div className="field">
            <label htmlFor="vehicle_id">ID kendaraan</label>
            <input
              id="vehicle_id"
              name="vehicle_id"
              type="text"
              placeholder="UUID kendaraan milikmu"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="available_seats">Jumlah kursi</label>
            <input id="available_seats" name="available_seats" type="number" min={1} defaultValue={3} required />
          </div>
          <div className="field">
            <label htmlFor="cost_per_seat">Biaya per kursi (Rp)</label>
            <input id="cost_per_seat" name="cost_per_seat" type="number" min={0} step={1000} defaultValue={0} required />
          </div>
          {error ? <ErrorNotice error={error} /> : null}
          <button className="button" type="submit" disabled={submitting}>
            {submitting ? "Memproses…" : "Publikasikan perjalanan"}
          </button>
        </form>
      </section>
    </main>
  );
}
