"use client";

import { useState } from "react";

import { getAuthErrorMessage, requestAuthApi } from "@/lib/auth/client";

export default function LogoutButton() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleLogout() {
    setPending(true);
    setError("");
    try {
      // Backend mencabut sesi di database dan menghapus cookie; endpoint ini idempotent.
      await requestAuthApi("/auth/logout", { method: "POST" });
      window.location.assign("/login");
    } catch (err) {
      setError(getAuthErrorMessage(err));
      setPending(false);
    }
  }

  return (
    <>
      <button className="link-button" type="button" onClick={handleLogout} disabled={pending}>
        {pending ? "Keluar…" : "Keluar"}
      </button>
      {error ? (
        <span className="field-error" role="alert">
          {error}
        </span>
      ) : null}
    </>
  );
}
