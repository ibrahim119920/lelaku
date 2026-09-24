import RegisterForm from "@/features/auth/register-form";

export default function RegisterPage() {
  return (
    <main className="page-shell">
      <section className="card auth-card">
        <div>
          <h1>Buat akun</h1>
          <p className="muted">Bergabung dan temukan teman seperjalanan.</p>
        </div>
        <RegisterForm />
      </section>
    </main>
  );
}
