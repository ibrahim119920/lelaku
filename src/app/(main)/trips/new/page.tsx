import Link from "next/link";

export default function NewTripPage() {
  return (
    <main className="page-shell">
      <section className="card">
        <p>
          <Link className="text-link" href="/trips">
            ← Kembali ke perjalanan
          </Link>
        </p>
        <h1>Buat perjalanan</h1>
        <p className="muted">
          Bagikan rencana perjalananmu dengan calon teman seperjalanan.
        </p>

        <form className="form-grid">
          <div className="field">
            <label htmlFor="origin">Titik keberangkatan</label>
            <input id="origin" name="origin" type="text" required />
          </div>
          <div className="field">
            <label htmlFor="destination">Tujuan</label>
            <input id="destination" name="destination" type="text" required />
          </div>
          <div className="field">
            <label htmlFor="departure">Waktu keberangkatan</label>
            <input id="departure" name="departure" type="datetime-local" required />
          </div>
          <div className="field">
            <label htmlFor="description">Deskripsi</label>
            <textarea id="description" name="description" rows={4} />
          </div>
          <button className="button" type="submit">
            Publikasikan perjalanan
          </button>
        </form>
      </section>
    </main>
  );
}
