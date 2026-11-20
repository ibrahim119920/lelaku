"use client";

import Link from "next/link";

import { ErrorNotice, StatusBadge } from "@/components/ui/error-notice";
import { RequestList } from "@/features/join-requests/request-list";
import { LocationLink } from "@/features/trips/trip-card";
import type { JoinedTrip, Trip } from "@/lib/api/types";
import { useApi } from "@/lib/api/use-api";
import { TRIP_STATUS_LABEL, formatDateTime } from "@/lib/format";

export default function RequestsView() {
  const published = useApi<Trip[]>("/trips/me/published");
  const joined = useApi<JoinedTrip[]>("/trips/me/joined");

  // Request hanya relevan di trip yang masih bisa menerima anggota.
  const openTrips = published.data?.filter((trip) => trip.status === "published") ?? [];

  return (
    <main className="page-shell stack">
      <section className="card">
        <h1>Permintaan bergabung</h1>
        <p className="muted">
          Permintaan masuk ke perjalananmu dan perjalanan yang kamu ikuti.
        </p>
      </section>

      <section className="stack">
        <h2>Permintaan masuk (sebagai driver)</h2>
        {published.loading ? <p className="muted">Memuat…</p> : null}
        {published.error ? <ErrorNotice error={published.error} /> : null}
        {published.data && openTrips.length === 0 ? (
          <p className="muted">Belum ada perjalanan terbuka yang kamu publikasikan.</p>
        ) : null}
        {openTrips.map((trip) => (
          <article className="card stack" key={trip.trip_id}>
            <div className="row">
              <strong>{formatDateTime(trip.departure_time)}</strong>
              <Link className="text-link" href={`/trips/${trip.trip_id}`}>
                Lihat trip
              </Link>
            </div>
            <LocationLink label="Tujuan" point={trip.destination} />
            <RequestList tripId={trip.trip_id} status="pending" />
          </article>
        ))}
      </section>

      <section className="stack">
        <h2>Perjalanan yang kuikuti</h2>
        {joined.loading ? <p className="muted">Memuat…</p> : null}
        {joined.error ? <ErrorNotice error={joined.error} /> : null}
        {joined.data && joined.data.length === 0 ? (
          <p className="muted">Kamu belum bergabung di perjalanan mana pun.</p>
        ) : null}
        {joined.data?.map((trip) => (
          <article className="card stack" key={trip.trip_id}>
            <div className="row">
              <strong>{formatDateTime(trip.departure_time)}</strong>
              <StatusBadge
                label={
                  trip.member_status === "cancelled"
                    ? "Dibatalkan"
                    : TRIP_STATUS_LABEL[trip.status]
                }
                tone={trip.member_status === "cancelled" ? "cancelled" : trip.status}
              />
            </div>
            <div className="actions inline">
              <Link className="button secondary" href={`/trips/${trip.trip_id}`}>
                Detail
              </Link>
              {trip.member_status === "active" ? (
                <Link className="button secondary" href={`/chat/${trip.trip_id}`}>
                  Chat
                </Link>
              ) : null}
            </div>
          </article>
        ))}
        <p className="muted">
          Catatan: request yang masih menunggu persetujuan belum bisa ditampilkan karena
          backend belum punya endpoint untuk itu.
        </p>
      </section>
    </main>
  );
}
