import ProfileForm from "@/features/auth/profile-form";
import { getCurrentProfile } from "@/lib/server/auth";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const profile = await getCurrentProfile();

  if (!profile) {
    return (
      <main className="page-shell">
        <section className="card" role="alert">
          <h1>Profil belum dapat dimuat</h1>
          <p className="muted">
            Layanan profile belum tersedia atau session sudah berakhir. Muat ulang halaman
            setelah layanan backend terhubung.
          </p>
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
