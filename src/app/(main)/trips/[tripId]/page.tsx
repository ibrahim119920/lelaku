import Link from "next/link";

export default function TripDetailPage() {
  return (
    <main className="page-shell">
      <section className="card stack">
        <p>
          <Link className="text-link" href="/trips">
            ← Kembali ke perjalanan
          </Link>
        </p>
        <div>
          <h1>Detail perjalanan</h1>
          <p className="muted">
            Informasi perjalanan dengan ID akan ditampilkan di sini.
          </p>
        </div>
        <div className="actions">
          <button className="button" type="button">
            Ajukan untuk bergabung
          </button>
          <Link className="button secondary" href="/chat/trip-id">
            Buka chat
          </Link>
        </div>
      </section>
    </main>
  );
}
