import Link from "next/link";

import { StatusBadge } from "@/components/ui/error-notice";
import { TRIP_STATUS_LABEL, formatDateTime, formatRupiah } from "@/lib/format";
import type { LatLng, Trip } from "@/lib/api/types";

export function LocationLink({ label, point }: { label: string; point: LatLng }) {
  const { lat, lng } = point;
  return (
    <a
      className="text-link"
      href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=15/${lat}/${lng}`}
      target="_blank"
      rel="noreferrer"
    >
      {label} ({lat.toFixed(4)}, {lng.toFixed(4)})
    </a>
  );
}

export function TripCard({ trip, extra }: { trip: Trip; extra?: React.ReactNode }) {
  return (
    <article className="card stack">
      <div className="row">
        <strong>{formatDateTime(trip.departure_time)}</strong>
        <StatusBadge label={TRIP_STATUS_LABEL[trip.status]} tone={trip.status} />
      </div>
      <div className="stack tight">
        <LocationLink label="Asal" point={trip.origin} />
        <LocationLink label="Tujuan" point={trip.destination} />
      </div>
      <p className="muted">
        {trip.available_seats} kursi tersedia · {formatRupiah(trip.cost_per_seat)} / kursi
      </p>
      {extra}
      <div>
        <Link className="button secondary" href={`/trips/${trip.trip_id}`}>
          Lihat detail
        </Link>
      </div>
    </article>
  );
}
