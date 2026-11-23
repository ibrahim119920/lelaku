import Link from "next/link";

import type { ApiError } from "@/lib/api/client";

export function ErrorNotice({ error }: { error: ApiError | string }) {
  const message = typeof error === "string" ? error : error.message;
  const unauthenticated = typeof error !== "string" && error.status === 401;

  return (
    <p className="form-status error" role="alert">
      {unauthenticated ? (
        <>
          Kamu belum login.{" "}
          <Link className="text-link" href="/login">
            Masuk
          </Link>{" "}
          untuk melanjutkan.
        </>
      ) : (
        message
      )}
    </p>
  );
}

export function StatusBadge({ label, tone }: { label: string; tone?: string }) {
  return <span className={`badge${tone ? ` ${tone}` : ""}`}>{label}</span>;
}
