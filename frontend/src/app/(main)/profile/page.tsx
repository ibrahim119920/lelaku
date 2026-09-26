import Link from "next/link";

import ProfileForm from "@/features/auth/profile-form";
import { getCurrentProfile, requireCurrentUser } from "@/lib/server/auth";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  await requireCurrentUser();
  const profile = await getCurrentProfile();

  if (!profile) {
    return (
      <main className="page-shell">
        <section className="card" role="alert">
          <h1>Profil belum dapat dimuat</h1>
          <p className="muted">
            Profil belum dapat dimuat. Coba muat ulang halaman atau masuk kembali jika sesi
            sudah berakhir.
          </p>
          <Link className="text-link" href="/login">
            Masuk kembali
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="card stack">
        <div>
          <h1>Profil</h1>
          <p className="muted">Kelola informasi dasar dan lihat status identitasmu.</p>
        </div>
        <ProfileForm initialProfile={profile} />
      </section>
    </main>
  );
}
