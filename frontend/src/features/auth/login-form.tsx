"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import {
  AuthApiError,
  getAuthErrorMessage,
  requestAuthApi,
} from "@/lib/auth/client";
import type { LoginInput } from "@/lib/auth/types";

type LoginField = keyof LoginInput;
type LoginErrors = Partial<Record<LoginField, string>>;

function validateLogin(input: LoginInput): LoginErrors {
  const errors: LoginErrors = {};

  if (!input.email) {
    errors.email = "Email wajib diisi.";
  } else if (!/^\S+@\S+\.\S+$/.test(input.email)) {
    errors.email = "Masukkan email yang valid.";
  }

  if (!input.password) {
    errors.password = "Kata sandi wajib diisi.";
  }

  return errors;
}

function getServerFieldErrors(error: unknown): LoginErrors {
  if (!(error instanceof AuthApiError)) {
    return {};
  }

  return {
    email: error.fields.email,
    password: error.fields.password,
  };
}

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<LoginErrors>({});
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const input: LoginInput = {
      email: email.trim().toLowerCase(),
      password,
    };
    const validationErrors = validateLogin(input);

    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      await requestAuthApi("/auth/login", {
        method: "POST",
        body: JSON.stringify(input),
      });
      window.location.assign("/");
    } catch (error) {
      setErrors(getServerFieldErrors(error));
      setFormError(
        error instanceof AuthApiError && error.status === 401
          ? "Email atau kata sandi salah."
          : getAuthErrorMessage(error),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <form className="form-grid" onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? "login-email-error" : undefined}
            required
          />
          {errors.email ? (
            <p className="field-error" id="login-email-error">
              {errors.email}
            </p>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="password">Kata sandi</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? "login-password-error" : undefined}
            required
          />
          {errors.password ? (
            <p className="field-error" id="login-password-error">
              {errors.password}
            </p>
          ) : null}
        </div>

        {formError ? (
          <p className="form-status error" role="alert">
            {formError}
          </p>
        ) : null}

        <button className="button" type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
          {isSubmitting ? "Memproses..." : "Masuk"}
        </button>
      </form>

      <p className="muted">
        Belum punya akun?{" "}
        <Link className="text-link" href="/register">
          Daftar
        </Link>
      </p>
    </>
  );
}
