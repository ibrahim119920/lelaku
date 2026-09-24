export type IdentityStatus = "verified" | "unverified";

export type UserProfile = {
  user_id: string;
  name: string;
  email: string;
  phone: string | null;
  profile_photo: string | null;
  identity_status: IdentityStatus;
  avg_rating: number | null;
  total_ratings: number;
  total_trips_completed: number;
};

export type RegisterInput = {
  name: string;
  email: string;
  phone: string;
  password: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type ProfileUpdateInput = {
  name: string;
  phone: string;
};

export type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    fields?: Record<string, string>;
  };
  message?: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nullableString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function nullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function nonNegativeInteger(value: unknown): number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0
    ? value
    : 0;
}

/**
 * Unwrap the response envelope used by the auth/profile contract.
 */
export function unwrapApiData(value: unknown): unknown {
  if (isRecord(value) && "data" in value) {
    return value.data;
  }

  return value;
}

/**
 * Extract a public user from an auth response without ever forwarding
 * password_hash or other fields returned accidentally by the backend.
 */
export function parseUserProfile(value: unknown): UserProfile | null {
  let candidate = unwrapApiData(value);

  if (isRecord(candidate) && "user" in candidate) {
    candidate = candidate.user;
  }

  if (!isRecord(candidate)) {
    return null;
  }

  const userId = candidate.user_id;
  const name = candidate.name;
  const email = candidate.email;
  const identityStatus = candidate.identity_status;

  if (
    typeof userId !== "string" ||
    userId.length === 0 ||
    typeof name !== "string" ||
    typeof email !== "string" ||
    (identityStatus !== "verified" && identityStatus !== "unverified")
  ) {
    return null;
  }

  return {
    user_id: userId,
    name,
    email,
    phone: nullableString(candidate.phone),
    profile_photo: nullableString(candidate.profile_photo),
    identity_status: identityStatus,
    avg_rating: nullableNumber(candidate.avg_rating),
    total_ratings: nonNegativeInteger(candidate.total_ratings),
    total_trips_completed: nonNegativeInteger(candidate.total_trips_completed),
  };
}

export function getApiErrorPayload(value: unknown): ApiErrorPayload {
  if (!isRecord(value)) {
    return {};
  }

  const error = isRecord(value.error) ? value.error : undefined;
  let fields: Record<string, string> | undefined;
  if (error && isRecord(error.fields)) {
    fields = {};
    for (const [key, fieldValue] of Object.entries(error.fields)) {
      if (typeof fieldValue === "string") {
        fields[key] = fieldValue;
      }
    }
  }

  return {
    message: typeof value.message === "string" ? value.message : undefined,
    error: error
      ? {
          code: typeof error.code === "string" ? error.code : undefined,
          message: typeof error.message === "string" ? error.message : undefined,
          fields,
        }
      : undefined,
  };
}
