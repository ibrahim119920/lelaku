import TripsView from "@/features/trips/trips-view";
import { requireCurrentUser } from "@/lib/server/auth";

// Guard dijalankan di server pada setiap render halaman (bukan hanya di layout, yang bisa
// dipakai ulang saat navigasi client). Tanpa sesi valid -> redirect ke /login.
export default async function TripsPage() {
  await requireCurrentUser();
  return <TripsView />;
}
