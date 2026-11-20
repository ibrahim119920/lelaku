"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { ErrorNotice } from "@/components/ui/error-notice";
import { TripCard } from "@/features/trips/trip-card";
import { geocode } from "@/lib/api/geocode";
import type { Trip } from "@/lib/api/types";
import { useApi } from "@/lib/api/use-api";

export default function TripsView() {
  const [path, setPath] = useState("/trips?limit=50");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const { data, error, loading } = useApi<Trip[]>(path);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const origin = String(form.get("origin") ?? "").trim();
    const destination = String(form.get("destination") ?? "").trim();
    const date = String(form.get("date") ?? "");
    const time = String(form.get("time") ?? "");

    if (time && !date) {
      setSearchError("Isi tanggal kalau ingin memfilter jam.");
      return;
    }

    setSearching(true);
    setSearchError("");
    try {
      const params = new URLSearchParams({ limit: "50" });
      // Geocoding berurutan (bukan paralel) agar patuh batas 1 request/detik Nominatim.
      if (origin) {
        const point = await geocode(origin);
        params.set("origin_lat", String(point.lat));
        params.set("origin_lng", String(point.lng));
      }
      if (destination) {
        const point = await geocode(destination);
        params.set("destination_lat", String(point.lat));
        params.set("destination_lng", String(point.lng));
      }
      if (date) params.set("date", date);
      if (date && time) params.set("time", time);
      setPath(`/trips?${params}`);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "Pencarian gagal.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <main className="page-shell stack">
      <section className="card">
        <h1>Perjalanan</h1>
        <p className="muted">Temukan perjalanan yang sesuai dengan rencanamu.</p>

        <form className="form-grid search-form" onSubmit={handleSearch}>
          <div className="field">
            <label htmlFor="origin">Asal</label>
            <input id="origin" name="origin" type="text" placeholder="mis. Bulaksumur, Yogyakarta" />
          </div>
          <div className="field">
            <label htmlFor="destination">Tujuan</label>
            <input id="destination" name="destination" type="text" placeholder="mis. Stasiun Tugu" />
          </div>
          <div className="field">
            <label htmlFor="date">Tanggal</label>
            <input id="date" name="date" type="date" />
          </div>
          <div className="field">
            <label htmlFor="time">Jam (±2 jam)</label>
            <input id="time" name="time" type="time" />
          </div>
          {searchError ? <ErrorNotice error={searchError} /> : null}
          <div className="actions">
            <button className="button" type="submit" disabled={searching}>
              {searching ? "Mencari lokasi…" : "Cari perjalanan"}
            </button>
            <Link className="button secondary" href="/trips/new">
              Buat perjalanan baru
            </Link>
          </div>
        </form>
      </section>

      {loading ? <p className="muted">Memuat perjalanan…</p> : null}
      {error ? <ErrorNotice error={error} /> : null}
      {data && data.length === 0 ? (
        <section className="card">
          <h2>Belum ada perjalanan</h2>
          <p className="muted">Tidak ada perjalanan yang cocok dengan pencarianmu.</p>
        </section>
      ) : null}
      {data?.map((trip) => <TripCard key={trip.trip_id} trip={trip} />)}
    </main>
  );
}
