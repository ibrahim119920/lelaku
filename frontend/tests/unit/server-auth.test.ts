import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { cookiesMock, fetchMock, redirectMock } = vi.hoisted(() => ({
  cookiesMock: vi.fn(),
  fetchMock: vi.fn(),
  redirectMock: vi.fn((path: string) => {
    throw new Error(`redirect:${path}`);
  }),
}));

vi.mock("next/headers", () => ({ cookies: cookiesMock }));
vi.mock("next/navigation", () => ({ redirect: redirectMock }));

import {
  AuthBackendUnavailableError,
  getCurrentUser,
  requireCurrentUser,
} from "../../src/lib/server/auth";

const publicUser = {
  user_id: "user-1",
  name: "Naya Pengguna",
  email: "naya@example.com",
  phone: "+628123456789",
  profile_photo: null,
  identity_status: "unverified",
  avg_rating: null,
  total_ratings: 0,
  total_trips_completed: 0,
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("server-side auth checks", () => {
  beforeEach(() => {
    vi.stubEnv("BACKEND_API_URL", "http://backend.test");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://backend.test");
    cookiesMock.mockReset();
    cookiesMock.mockResolvedValue({
      get: vi.fn(() => ({ value: "opaque-session-token" })),
    });
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    redirectMock.mockClear();
    redirectMock.mockImplementation((path: string) => {
      throw new Error(`redirect:${path}`);
    });
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("rechecks the session on each protected page request", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(200, { data: publicUser }))
      .mockResolvedValueOnce(
        jsonResponse(401, {
          error: { code: "AUTH_UNAUTHENTICATED", message: "Sesi berakhir." },
        }),
      );

    const firstRequestUser = await requireCurrentUser();
    expect(firstRequestUser.user_id).toBe("user-1");

    await expect(requireCurrentUser()).rejects.toThrow("redirect:/login");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0][0]).toBe("http://backend.test/auth/me");
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ cache: "no-store" });
  });

  it("redirects only for a missing or rejected session", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(401, { error: { code: "AUTH_UNAUTHENTICATED" } }));

    await expect(requireCurrentUser()).rejects.toThrow("redirect:/login");
    expect(redirectMock).toHaveBeenCalledWith("/login");
  });

  it("does not treat backend 5xx as an unauthenticated session", async () => {
    fetchMock.mockResolvedValueOnce(new Response("unavailable", { status: 503 }));

    await expect(requireCurrentUser()).rejects.toBeInstanceOf(AuthBackendUnavailableError);
    expect(redirectMock).not.toHaveBeenCalled();
  });

  it("does not treat a network failure as an unauthenticated session", async () => {
    fetchMock.mockRejectedValueOnce(new Error("connection refused"));

    await expect(getCurrentUser()).rejects.toBeInstanceOf(AuthBackendUnavailableError);
    expect(redirectMock).not.toHaveBeenCalled();
  });

  it("redirects without calling the backend when no session cookie exists", async () => {
    cookiesMock.mockResolvedValueOnce({ get: vi.fn(() => undefined) });

    await expect(requireCurrentUser()).rejects.toThrow("redirect:/login");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
