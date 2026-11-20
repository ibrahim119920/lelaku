"use client";

import { useEffect, useState } from "react";

import { ErrorNotice, StatusBadge } from "@/components/ui/error-notice";
import { apiFetch, toApiError, type ApiError } from "@/lib/api/client";
import { useApi } from "@/lib/api/use-api";
import type { RideRequest, RideRequestWithRequester } from "@/lib/api/types";
import { REQUEST_STATUS_LABEL, formatDateTime } from "@/lib/format";

type Props = {
  tripId: string;
  /** Hanya tampilkan request dengan status ini (default: semua). */
  status?: RideRequest["status"];
  /** Dipanggil kalau user terbukti driver pemilik trip (GET berhasil). */
  onDriverConfirmed?: () => void;
  /** Dipanggil kalau server membalas 403 (user bukan driver trip ini). */
  onForbidden?: () => void;
  /** Dipanggil setelah accept/reject berhasil (mis. untuk muat ulang kursi & anggota). */
  onDecided?: () => void;
};

/** Daftar request masuk untuk driver (FR-12), lengkap dengan tombol terima/tolak. */
export function RequestList({ tripId, status, onDriverConfirmed, onForbidden, onDecided }: Props) {
  const path = `/trips/${tripId}/requests${status ? `?status=${status}` : ""}`;
  const { data, error, loading, reload } = useApi<RideRequestWithRequester[]>(path);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (data) onDriverConfirmed?.();
  }, [data, onDriverConfirmed]);

  useEffect(() => {
    if (error?.status === 403) onForbidden?.();
  }, [error, onForbidden]);

  async function decide(requestId: string, decision: "accepted" | "rejected") {
    setBusyId(requestId);
    setActionError(null);
    try {
      await apiFetch(`/trips/${tripId}/requests/${requestId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: decision }),
      });
      reload();
      onDecided?.();
    } catch (err) {
      setActionError(toApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  // 403 berarti bukan driver trip ini: komponen sengaja tidak menampilkan apa-apa.
  if (error?.status === 403) return null;
  if (loading && !data) return <p className="muted">Memuat permintaan…</p>;
  if (error) return <ErrorNotice error={error} />;
  if (!data) return null;

  return (
    <section className="stack">
      <h2>Permintaan bergabung</h2>
      {actionError ? <ErrorNotice error={actionError} /> : null}
      {data.length === 0 ? <p className="muted">Belum ada permintaan.</p> : null}
      {data.map((request) => (
        <div className="request-item" key={request.request_id}>
          <div className="row">
            <strong>{request.requester.name}</strong>
            <StatusBadge
              label={REQUEST_STATUS_LABEL[request.status]}
              tone={request.status}
            />
          </div>
          <p className="muted">
            Jemput: {request.pickup} · Rating {request.requester.avg_rating.toFixed(1)} (
            {request.requester.total_ratings}) · {formatDateTime(request.created_at)}
          </p>
          {request.status === "pending" ? (
            <div className="actions">
              <button
                className="button"
                type="button"
                disabled={busyId === request.request_id}
                onClick={() => decide(request.request_id, "accepted")}
              >
                Terima
              </button>
              <button
                className="button secondary"
                type="button"
                disabled={busyId === request.request_id}
                onClick={() => decide(request.request_id, "rejected")}
              >
                Tolak
              </button>
            </div>
          ) : null}
        </div>
      ))}
    </section>
  );
}
