import { getApiErrorPayload } from "@/lib/auth/types";

export class AuthApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly fields: Record<string, string>;

  constructor(
    message: string,
    status: number,
    options?: { code?: string; fields?: Record<string, string> },
  ) {
    super(message);
    this.name = "AuthApiError";
    this.status = status;
    this.code = options?.code;
    this.fields = options?.fields ?? {};
  }
}

function getApiUrl(path: string): string {
  const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
  return `${baseUrl}${path}`;
}

async function readResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return response.json();
}

export async function requestAuthApi<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(getApiUrl(path), {
      ...init,
      credentials: "include",
      headers,
    });
  } catch {
    throw new AuthApiError(
      "Layanan belum dapat dihubungi. Periksa koneksi lalu coba lagi.",
      0,
    );
  }

  const body = await readResponseBody(response);

  if (!response.ok) {
    const payload = getApiErrorPayload(body);
    throw new AuthApiError(
      payload.error?.message ?? payload.message ?? "Permintaan tidak dapat diproses.",
      response.status,
      {
        code: payload.error?.code,
        fields: payload.error?.fields,
      },
    );
  }

  return body as T;
}

export function getAuthErrorMessage(error: unknown): string {
  if (error instanceof AuthApiError) {
    return error.message;
  }

  return "Terjadi kesalahan. Coba lagi.";
}
