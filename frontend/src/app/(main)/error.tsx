"use client";

export default function MainError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="page-shell">
      <section className="card stack" role="alert">
        <h1>Halaman belum dapat dimuat</h1>
        <p className="muted">
          Layanan mungkin sedang terganggu. Coba lagi sebentar lagi; kamu tidak perlu masuk
          ulang kecuali sesi memang sudah berakhir.
        </p>
        <button className="button" type="button" onClick={reset}>
          Coba lagi
        </button>
      </section>
    </main>
  );
}
