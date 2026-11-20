import { describe, expect, it } from "vitest";

import { getApiErrorPayload, parseUserProfile } from "../../src/lib/auth/types";

const backendUser = {
  user_id: "user-123",
  name: "Nama Pengguna",
  email: "user@example.com",
  phone: "+628123456789",
  profile_photo: null,
  identity_status: "unverified",
  avg_rating: null,
  total_ratings: 0,
  total_trips_completed: 0,
  password_hash: "$argon2id$should-never-leave-the-server",
};

describe("auth/profile public DTO", () => {
  it("unwraps the response and strips password_hash", () => {
    const publicUser = parseUserProfile({ data: { user: backendUser } });

    expect(publicUser).toEqual({
      user_id: "user-123",
      name: "Nama Pengguna",
      email: "user@example.com",
      phone: "+628123456789",
      profile_photo: null,
      identity_status: "unverified",
      avg_rating: null,
      total_ratings: 0,
      total_trips_completed: 0,
    });
    expect(publicUser).not.toHaveProperty("password_hash");
  });

  it("rejects an unknown identity status instead of guessing", () => {
    expect(
      parseUserProfile({ ...backendUser, identity_status: "pending" }),
    ).toBeNull();
  });

  it("keeps only string field errors from an API error response", () => {
    expect(
      getApiErrorPayload({
        error: {
          code: "VALIDATION_ERROR",
          message: "Periksa kembali input.",
          fields: { email: "Email tidak valid.", password: 123 },
        },
      }),
    ).toEqual({
      error: {
        code: "VALIDATION_ERROR",
        message: "Periksa kembali input.",
        fields: { email: "Email tidak valid." },
      },
    });
  });
});
