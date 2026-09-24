import Link from "next/link";
import type { ReactNode } from "react";

import { requireCurrentUser } from "@/lib/server/auth";

export default async function MainLayout({ children }: { children: ReactNode }) {
  await requireCurrentUser();

  return (
    <>
      <header className="site-header">
        <Link className="brand" href="/">
          Lelaku
        </Link>
        <nav className="site-nav" aria-label="Navigasi utama">
          <Link href="/trips">Perjalanan</Link>
          <Link href="/requests">Permintaan</Link>
          <Link href="/profile">Profil</Link>
        </nav>
      </header>
      {children}
    </>
  );
}
