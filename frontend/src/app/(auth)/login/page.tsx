import LoginForm from "@/features/auth/login-form";

export default function LoginPage() {
  return (
    <main className="page-shell">
      <section className="card auth-card">
        <div>
          <h1>Masuk</h1>
          <p className="muted">Masuk untuk mengelola perjalanan dan permintaanmu.</p>
        </div>
        <LoginForm />
      </section>
    </main>
  );
}
