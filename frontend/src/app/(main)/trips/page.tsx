import Link from "next/link";

import { requireCurrentUser } from "@/lib/server/auth";

export default async function TripsPage() {
  await requireCurrentUser();

  return (
    <main className="page-shell stack">
      <section className="card">
        <h1>Perjalanan</h1>
        <p className="muted">Temukan perjalanan yang sesuai dengan rencanamu.</p>
        <div className="actions">
          <Link className="button" href="/trips/new">
            Buat perjalanan baru
          </Link>
        </div>
      </section>

      <section className="card">
        <h2>Belum ada perjalanan</h2>
        <p className="muted">Daftar perjalanan akan ditampilkan di sini.</p>
      </section>
    </main>
  );
}
