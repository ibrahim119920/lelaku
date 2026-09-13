import Link from "next/link";

export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card stack">
        <div>
          <p className="brand">Lelaku</p>
          <h1>Buat akun</h1>
          <p className="muted">Bergabung dan temukan teman seperjalanan.</p>
        </div>

        <form className="form-grid">
          <div className="field">
            <label htmlFor="name">Nama</label>
            <input id="name" name="name" type="text" required />
          </div>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" required />
          </div>
          <div className="field">
            <label htmlFor="password">Kata sandi</label>
            <input id="password" name="password" type="password" required />
          </div>
          <button className="button" type="submit">
            Daftar
          </button>
        </form>

        <p className="muted">
          Sudah punya akun?{" "}
          <Link className="text-link" href="/login">
            Masuk
          </Link>
        </p>
      </section>
    </main>
  );
}
