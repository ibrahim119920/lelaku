import RegisterForm from "@/features/auth/register-form";

export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card stack">
        <div>
          <p className="brand">Lelaku</p>
          <h1>Buat akun</h1>
          <p className="muted">Bergabung dan temukan teman seperjalanan.</p>
        </div>
        <RegisterForm />
      </section>
    </main>
  );
}
