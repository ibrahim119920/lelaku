export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError(
    0,
    error instanceof Error ? error.message : "Terjadi kesalahan tak terduga.",
  );
}

// Backend trip/chat memakai { detail: string | [{ msg }] }; modul auth memakai
// { error: { message } }. Dua-duanya ditangani supaya pesan selalu tampil.
function extractMessage(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null) return fallback;
  const record = body as Record<string, unknown>;

  if (typeof record.detail === "string") return record.detail;
  if (Array.isArray(record.detail)) {
    const messages = record.detail
      .map((item) =>
        typeof item === "object" && item !== null && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : null,
      )
      .filter(Boolean);
    if (messages.length > 0) return messages.join("; ");
  }
  const nested = record.error;
  if (typeof nested === "object" && nested !== null && "message" in nested) {
    return String((nested as { message: unknown }).message);
  }
  return fallback;
}

/**
 * Panggil API backend. Cookie sesi (httpOnly) dikirim lewat `credentials: "include"`.
 * Melempar ApiError dengan pesan bahasa Indonesia dari server.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      credentials: "include",
    });
  } catch {
    throw new ApiError(0, "Tidak bisa terhubung ke server. Pastikan backend berjalan.");
  }

  if (response.status === 204) return undefined as T;

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      response.status,
      extractMessage(body, `Permintaan gagal (${response.status}).`),
    );
  }
  return body as T;
}

export function jsonBody(value: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(value) };
}
