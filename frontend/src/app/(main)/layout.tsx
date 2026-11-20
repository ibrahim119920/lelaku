import Link from "next/link";
import type { ReactNode } from "react";

import LogoutButton from "@/features/auth/logout-button";

export default function MainLayout({ children }: { children: ReactNode }) {
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
          <LogoutButton />
        </nav>
      </header>
      {children}
    </>
  );
}
