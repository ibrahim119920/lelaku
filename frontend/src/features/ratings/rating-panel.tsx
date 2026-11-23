"use client";

import { useState } from "react";

import { ErrorNotice } from "@/components/ui/error-notice";
import { apiFetch, jsonBody, toApiError, type ApiError } from "@/lib/api/client";
import type { Rating, TripMember } from "@/lib/api/types";

type Props = { tripId: string; members: TripMember[] };

/**
 * Rating dua arah (FR-15). Frontend belum punya user_id sendiri, jadi role_context
 * diturunkan dari peran penerima; server yang memvalidasi apakah pasangan ini sah
 * (mis. merating diri sendiri ditolak 400).
 */
export function RatingPanel({ tripId, members }: Props) {
  return (
    <section className="stack">
      <h2>Beri rating</h2>
      <p className="muted">Trip sudah selesai. Pilih anggota yang ingin kamu nilai.</p>
      {members.map((member) => (
        <RatingRow key={member.user_id} tripId={tripId} member={member} />
      ))}
    </section>
  );
}

function RatingRow({ tripId, member }: { tripId: string; member: TripMember }) {
  const [score, setScore] = useState(5);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await apiFetch<Rating>(
        `/trips/${tripId}/ratings`,
        jsonBody({
          rated_user_id: member.user_id,
          role_context: member.role === "driver" ? "passenger_to_driver" : "driver_to_passenger",
          score,
        }),
      );
      setDone(true);
    } catch (err) {
      setError(toApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="request-item">
      <div className="row">
        <strong>
          {member.name} <span className="muted">({member.role})</span>
        </strong>
        {done ? (
          <span className="badge completed">Terkirim</span>
        ) : (
          <div className="actions inline">
            <select
              aria-label={`Skor untuk ${member.name}`}
              value={score}
              onChange={(event) => setScore(Number(event.target.value))}
            >
              {[5, 4, 3, 2, 1].map((value) => (
                <option key={value} value={value}>
                  {value} ★
                </option>
              ))}
            </select>
            <button className="button" type="button" disabled={busy} onClick={submit}>
              Kirim
            </button>
          </div>
        )}
      </div>
      {error ? <ErrorNotice error={error} /> : null}
    </div>
  );
}
