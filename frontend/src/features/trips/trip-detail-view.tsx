"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { ErrorNotice, StatusBadge } from "@/components/ui/error-notice";
import { RequestList } from "@/features/join-requests/request-list";
import { RatingPanel } from "@/features/ratings/rating-panel";
import { LocationLink, TripCard } from "@/features/trips/trip-card";
import { apiFetch, jsonBody, toApiError, type ApiError } from "@/lib/api/client";
import type { RecommendedTrip, TripDetail, TripMember, TripStatus } from "@/lib/api/types";
import { useApi } from "@/lib/api/use-api";
import { isChatParticipant } from "@/lib/chat";
import { TRIP_STATUS_LABEL, formatDateTime, formatRupiah } from "@/lib/format";

// Cermin ALLOWED_STATUS_TRANSITIONS di backend/app/trip/service.py.
const NEXT_STATUSES: Record<TripStatus, { status: "ongoing" | "completed" | "cancelled"; label: string }[]> = {
  published: [
    { status: "ongoing", label: "Mulai perjalanan" },
    { status: "cancelled", label: "Batalkan" },
  ],
  ongoing: [
    { status: "completed", label: "Selesaikan" },
    { status: "cancelled", label: "Batalkan" },
  ],
  completed: [],
  cancelled: [],
};

export default function TripDetailView({ currentUserId }: { currentUserId: string }) {
  const { tripId } = useParams<{ tripId: string }>();
  const trip = useApi<TripDetail>(`/trips/${tripId}`);
  const members = useApi<TripMember[]>(`/trips/${tripId}/members`);
  const recommended = useApi<RecommendedTrip[]>(`/trips/recommended?trip_id=${tripId}`);

  // null = belum diketahui. Backend tidak punya endpoint "siapa saya", jadi peran driver
  // disimpulkan dari GET /requests: berhasil = driver, 403 = bukan driver.
  const [isDriver, setIsDriver] = useState<boolean | null>(null);
  const markDriver = useCallback(() => setIsDriver(true), []);
  const markNotDriver = useCallback(() => setIsDriver(false), []);

  const [actionError, setActionError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  const refreshTrip = useCallback(() => {
    trip.reload();
    members.reload();
  }, [trip, members]);

  async function changeStatus(status: string) {
    setBusy(true);
    setActionError(null);
    try {
      await apiFetch(`/trips/${tripId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      refreshTrip();
    } catch (err) {
      setActionError(toApiError(err));
    } finally {
      setBusy(false);
    }
  }

  if (trip.loading && !trip.data) {
    return (
      <main className="page-shell">
        <p className="muted">Memuat perjalanan…</p>
      </main>
    );
  }
  if (trip.error || !trip.data) {
    return (
      <main className="page-shell stack">
        <p>
          <Link className="text-link" href="/trips">
            ← Kembali ke perjalanan
          </Link>
        </p>
        {trip.error ? <ErrorNotice error={trip.error} /> : null}
      </main>
    );
  }

  const detail = trip.data;
  const canChat = isChatParticipant(currentUserId, detail.driver.user_id, members.data);

  return (
    <main className="page-shell stack">
      <section className="card stack">
        <p>
          <Link className="text-link" href="/trips">
            ← Kembali ke perjalanan
          </Link>
        </p>
        <div className="row">
          <h1>Detail perjalanan</h1>
          <StatusBadge label={TRIP_STATUS_LABEL[detail.status]} tone={detail.status} />
        </div>

        <div className="stack tight">
          <LocationLink label="Asal" point={detail.origin} />
          <LocationLink label="Tujuan" point={detail.destination} />
          <p>Berangkat: {formatDateTime(detail.departure_time)}</p>
          <p>
            {detail.available_seats} kursi tersedia · {formatRupiah(detail.cost_per_seat)} / kursi
          </p>
        </div>

        <div className="stack tight">
          <h2>Driver &amp; kendaraan</h2>
          <p>
            {detail.driver.name} · Rating {detail.driver.avg_rating_driver.toFixed(1)} (
            {detail.driver.total_ratings_driver})
          </p>
          <p className="muted">
            {detail.vehicle.brand} {detail.vehicle.model} ({detail.vehicle.type}) ·{" "}
            {detail.vehicle.plate_number} · kapasitas {detail.vehicle.capacity}
          </p>
        </div>

        <div className="actions">
          {canChat ? (
            <Link className="button secondary" href={`/chat/${tripId}`}>
              Buka chat
            </Link>
          ) : null}
          {isDriver
            ? NEXT_STATUSES[detail.status].map((next) => (
                <button
                  key={next.status}
                  className="button"
                  type="button"
                  disabled={busy}
                  onClick={() => changeStatus(next.status)}
                >
                  {next.label}
                </button>
              ))
            : null}
        </div>
        {actionError ? <ErrorNotice error={actionError} /> : null}
        {!canChat && !members.loading ? (
          <p className="muted">
            Chat hanya tersedia untuk driver dan peserta yang sudah diterima.
          </p>
        ) : null}
      </section>

      {isDriver === false && detail.status === "published" ? (
        <JoinForm tripId={tripId} />
      ) : null}

      <section className="card">
        <RequestList
          tripId={tripId}
          onDriverConfirmed={markDriver}
          onForbidden={markNotDriver}
          onDecided={refreshTrip}
        />
        {isDriver === false ? <p className="muted">Hanya driver yang bisa melihat permintaan masuk.</p> : null}
      </section>

      <section className="card stack">
        <h2>Anggota perjalanan</h2>
        {members.error ? <ErrorNotice error={members.error} /> : null}
        {members.data?.map((member) => (
          <p key={member.user_id}>
            {member.name} <span className="muted">({member.role})</span>
          </p>
        ))}
      </section>

      {detail.status === "completed" && members.data ? (
        <section className="card">
          <RatingPanel tripId={tripId} members={members.data} />
        </section>
      ) : null}

      {recommended.data && recommended.data.length > 0 ? (
        <section className="stack">
          <h2>Perjalanan serupa</h2>
          {recommended.data.map((item) => (
            <TripCard
              key={item.trip.trip_id}
              trip={item.trip}
              extra={
                <p className="muted">
                  Kecocokan {Math.round(item.score * 100)}% · selisih waktu{" "}
                  {Math.round(item.time_diff_minutes)} menit
                </p>
              }
            />
          ))}
        </section>
      ) : null}
    </main>
  );
}

function JoinForm({ tripId }: { tripId: string }) {
  const [pickup, setPickup] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await apiFetch(`/trips/${tripId}/requests`, jsonBody({ pickup: pickup.trim() }));
      setSent(true);
    } catch (err) {
      setError(toApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2>Ajukan untuk bergabung</h2>
      {sent ? (
        <p className="form-status success">
          Permintaan terkirim. Lihat status atau batalkan di{" "}
          <Link className="text-link" href="/requests">
            Permintaan saya
          </Link>
          .
        </p>
      ) : (
        <form className="form-grid" onSubmit={submit}>
          <div className="field">
            <label htmlFor="pickup">Titik jemput</label>
            <input
              id="pickup"
              value={pickup}
              onChange={(event) => setPickup(event.target.value)}
              maxLength={255}
              required
            />
          </div>
          {error ? <ErrorNotice error={error} /> : null}
          <button className="button" type="submit" disabled={busy}>
            {busy ? "Mengirim…" : "Kirim permintaan"}
          </button>
        </form>
      )}
    </section>
  );
}
