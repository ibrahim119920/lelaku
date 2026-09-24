import Link from "next/link";

import { requireCurrentUser } from "@/lib/server/auth";

export default async function ChatPage() {
  await requireCurrentUser();

  return (
    <main className="page-shell">
      <section className="card stack">
        <p>
          <Link className="text-link" href="/trips">
            ← Kembali ke perjalanan
          </Link>
        </p>
        <h1>Chat perjalanan</h1>
        <p className="muted">
          Percakapan untuk perjalanan terpilih akan ditampilkan di sini.
        </p>
        <div className="field">
          <label htmlFor="message">Pesan</label>
          <textarea id="message" name="message" rows={4} placeholder="Tulis pesan..." />
        </div>
        <button className="button" type="button">
          Kirim pesan
        </button>
      </section>
    </main>
  );
}
