import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { parseUserProfile, type UserProfile } from "../auth/types";

const SESSION_COOKIE_NAME = "lelaku_session";

export type AuthUser = UserProfile;

export class AuthBackendUnavailableError extends Error {
  constructor() {
    super("Layanan Lelaku sedang tidak dapat dihubungi. Coba lagi beberapa saat.");
    this.name = "AuthBackendUnavailableError";
  }
}

function getBackendBaseUrl(): string | null {
  const baseUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!baseUrl) {
    return null;
  }

  return baseUrl.replace(/\/$/, "");
}

async function requestBackend(path: string, init: RequestInit = {}): Promise<Response | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);

  if (!sessionCookie?.value) {
    return null;
  }

  const baseUrl = getBackendBaseUrl();
  if (!baseUrl) {
    throw new AuthBackendUnavailableError();
  }

  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Cookie", SESSION_COOKIE_NAME + "=" + sessionCookie.value);

  try {
    return await fetch(baseUrl + path, {
      ...init,
      cache: "no-store",
      credentials: "include",
      headers,
    });
  } catch {
    throw new AuthBackendUnavailableError();
  }
}

async function parseJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const response = await requestBackend("/auth/me");

  if (!response || response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new AuthBackendUnavailableError();
  }

  const user = parseUserProfile(await parseJson(response));
  if (!user) {
    throw new AuthBackendUnavailableError();
  }

  return user;
}

export async function getCurrentProfile(): Promise<UserProfile | null> {
  const response = await requestBackend("/profile");

  if (!response || response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new AuthBackendUnavailableError();
  }

  const profile = parseUserProfile(await parseJson(response));
  if (!profile) {
    throw new AuthBackendUnavailableError();
  }

  return profile;
}

export async function requireCurrentUser(): Promise<AuthUser> {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  return user;
}
