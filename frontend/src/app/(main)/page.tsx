import Link from "next/link";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="brand">Lelaku</p>
        <h1>Perjalanan lebih berarti bersama teman seperjalanan.</h1>
        <p className="muted">
          Publikasikan rencana perjalanan, temukan partner yang cocok, dan
          berkoordinasi dengan aman.
        </p>
        <div className="actions">
          <Link className="button" href="/trips/new">
            Buat perjalanan
          </Link>
          <Link className="button secondary" href="/trips">
            Jelajahi perjalanan
          </Link>
        </div>
      </section>

      <section className="card">
        <h2>Mulai dari sini</h2>
        <p className="muted">
          Folder fitur, komponen bersama, database, dan pengujian sudah
          disiapkan untuk pengembangan berikutnya.
        </p>
      </section>
    </main>
  );
}
