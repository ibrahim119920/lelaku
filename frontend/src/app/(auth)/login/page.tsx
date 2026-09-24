import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card stack">
        <div>
          <p className="brand">Lelaku</p>
          <h1>Masuk</h1>
          <p className="muted">Masuk untuk mengelola perjalanan dan permintaanmu.</p>
        </div>

        <form className="form-grid">
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" required />
          </div>
          <div className="field">
            <label htmlFor="password">Kata sandi</label>
            <input id="password" name="password" type="password" required />
          </div>
          <button className="button" type="submit">
            Masuk
          </button>
        </form>

        <p className="muted">
          Belum punya akun?{" "}
          <Link className="text-link" href="/register">
            Daftar
          </Link>
        </p>
      </section>
    </main>
  );
}
