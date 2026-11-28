"use client";

import Link from "next/link";
import { useState } from "react";

import { ErrorNotice, StatusBadge } from "@/components/ui/error-notice";
import { RequestList } from "@/features/join-requests/request-list";
import { LocationLink } from "@/features/trips/trip-card";
import { apiFetch, toApiError, type ApiError } from "@/lib/api/client";
import type { JoinedTrip, MyRideRequest, Trip } from "@/lib/api/types";
import { useApi } from "@/lib/api/use-api";
import { REQUEST_STATUS_LABEL, TRIP_STATUS_LABEL, formatDateTime } from "@/lib/format";

export default function RequestsView() {
  const published = useApi<Trip[]>("/trips/me/published");
  const joined = useApi<JoinedTrip[]>("/trips/me/joined");
  const mine = useApi<MyRideRequest[]>("/trips/me/requests");
  const [cancelBusyId, setCancelBusyId] = useState<string | null>(null);
  const [cancelError, setCancelError] = useState<ApiError | null>(null);

  // Request hanya relevan di trip yang masih bisa menerima anggota.
  const openTrips = published.data?.filter((trip) => trip.status === "published") ?? [];

  async function cancelRequest(request: MyRideRequest) {
    setCancelBusyId(request.request_id);
    setCancelError(null);
    try {
      await apiFetch(`/trips/${request.trip_id}/requests/${request.request_id}`, {
        method: "DELETE",
      });
      mine.reload();
    } catch (err) {
      setCancelError(toApiError(err));
    } finally {
      setCancelBusyId(null);
    }
  }

  return (
    <main className="page-shell stack">
      <section className="card">
        <h1>Permintaan bergabung</h1>
        <p className="muted">
          Permintaan masuk sebagai driver dan permintaan yang kamu ajukan sebagai passenger.
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
        <h2>Permintaan saya</h2>
        {mine.loading ? <p className="muted">Memuat…</p> : null}
        {mine.error ? <ErrorNotice error={mine.error} /> : null}
        {cancelError ? <ErrorNotice error={cancelError} /> : null}
        {mine.data && mine.data.length === 0 ? (
          <p className="muted">Kamu belum pernah mengajukan permintaan bergabung.</p>
        ) : null}
        {mine.data?.map((request) => (
          <article className="card stack" key={request.request_id}>
            <div className="row">
              <strong>{formatDateTime(request.trip.departure_time)}</strong>
              <StatusBadge
                label={REQUEST_STATUS_LABEL[request.status]}
                tone={request.status}
              />
            </div>
            <LocationLink label="Tujuan" point={request.trip.destination} />
            <p className="muted">
              Jemput: {request.pickup} | Diajukan {formatDateTime(request.created_at)}
            </p>
            <div className="actions inline">
              <Link className="button secondary" href={`/trips/${request.trip_id}`}>
                Detail
              </Link>
              {request.status === "pending" ? (
                <button
                  className="button secondary"
                  type="button"
                  disabled={cancelBusyId === request.request_id}
                  onClick={() => cancelRequest(request)}
                >
                  {cancelBusyId === request.request_id ? "Membatalkan…" : "Batalkan"}
                </button>
              ) : null}
            </div>
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
      </section>
    </main>
  );
}
