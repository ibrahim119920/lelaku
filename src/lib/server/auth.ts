import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { parseUserProfile, type UserProfile } from "@/lib/auth/types";

const SESSION_COOKIE_NAME = "lelaku_session";

export type AuthUser = UserProfile;

function getBackendBaseUrl(): string | null {
  const baseUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!baseUrl) {
    return null;
  }

  return baseUrl.replace(/\/$/, "");
}

async function requestBackend(path: string, init: RequestInit = {}): Promise<Response | null> {
  const baseUrl = getBackendBaseUrl();
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);

  if (!baseUrl || !sessionCookie?.value) {
    return null;
  }

  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Cookie", cookieHeader);

  try {
    return await fetch(`${baseUrl}${path}`, {
      ...init,
      cache: "no-store",
      credentials: "include",
      headers,
    });
  } catch {
    return null;
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

  if (!response?.ok) {
    return null;
  }

  return parseUserProfile(await parseJson(response));
}

export async function getCurrentProfile(): Promise<UserProfile | null> {
  const response = await requestBackend("/profile");

  if (!response?.ok) {
    return null;
  }

  return parseUserProfile(await parseJson(response));
}

export async function requireCurrentUser(): Promise<AuthUser> {
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  return user;
}
