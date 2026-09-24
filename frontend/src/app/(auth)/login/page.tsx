import LoginForm from "@/features/auth/login-form";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card stack">
        <div>
          <p className="brand">Lelaku</p>
          <h1>Masuk</h1>
          <p className="muted">Masuk untuk mengelola perjalanan dan permintaanmu.</p>
        </div>
        <LoginForm />
      </section>
    </main>
  );
}
