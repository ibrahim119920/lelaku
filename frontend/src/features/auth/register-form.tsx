"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import {
  AuthApiError,
  getAuthErrorMessage,
  requestAuthApi,
} from "@/lib/auth/client";
import type { RegisterInput } from "@/lib/auth/types";

type RegisterField = keyof RegisterInput;
type RegisterErrors = Partial<Record<RegisterField, string>>;

function validateRegister(input: RegisterInput): RegisterErrors {
  const errors: RegisterErrors = {};

  if (input.name.length < 2) {
    errors.name = "Nama minimal terdiri dari 2 karakter.";
  }

  if (!input.email) {
    errors.email = "Email wajib diisi.";
  } else if (!/^\S+@\S+\.\S+$/.test(input.email)) {
    errors.email = "Masukkan email yang valid.";
  }

  if (!input.phone) {
    errors.phone = "Nomor telepon wajib diisi.";
  }

  if (input.password.length < 8) {
    errors.password = "Kata sandi minimal terdiri dari 8 karakter.";
  }

  return errors;
}

function getServerFieldErrors(error: unknown): RegisterErrors {
  if (!(error instanceof AuthApiError)) {
    return {};
  }

  return {
    name: error.fields.name,
    email: error.fields.email,
    phone: error.fields.phone,
    password: error.fields.password,
  };
}

export default function RegisterForm() {
  const [form, setForm] = useState<RegisterInput>({
    name: "",
    email: "",
    phone: "",
    password: "",
  });
  const [errors, setErrors] = useState<RegisterErrors>({});
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field: RegisterField, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setFormError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");
    setSuccessMessage("");

    const input: RegisterInput = {
      name: form.name.trim(),
      email: form.email.trim().toLowerCase(),
      phone: form.phone.trim(),
      password: form.password,
    };
    const validationErrors = validateRegister(input);

    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      await requestAuthApi("/auth/register", {
        method: "POST",
        body: JSON.stringify(input),
      });
      setForm({ name: "", email: "", phone: "", password: "" });
      setErrors({});
      setSuccessMessage("Akun berhasil dibuat. Silakan masuk dengan akunmu.");
    } catch (error) {
      setErrors(getServerFieldErrors(error));
      setFormError(
        error instanceof AuthApiError && error.code === "EMAIL_ALREADY_EXISTS"
          ? "Email sudah terdaftar. Gunakan email lain atau masuk."
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
          <label htmlFor="name">Nama</label>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            value={form.name}
            onChange={(event) => updateField("name", event.target.value)}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "register-name-error" : undefined}
            required
          />
          {errors.name ? (
            <p className="field-error" id="register-name-error">
              {errors.name}
            </p>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            value={form.email}
            onChange={(event) => updateField("email", event.target.value)}
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? "register-email-error" : undefined}
            required
          />
          {errors.email ? (
            <p className="field-error" id="register-email-error">
              {errors.email}
            </p>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="phone">Nomor telepon</label>
          <input
            id="phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            inputMode="tel"
            value={form.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            aria-invalid={Boolean(errors.phone)}
            aria-describedby={errors.phone ? "register-phone-error" : undefined}
            required
          />
          {errors.phone ? (
            <p className="field-error" id="register-phone-error">
              {errors.phone}
            </p>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="password">Kata sandi</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={8}
            value={form.password}
            onChange={(event) => updateField("password", event.target.value)}
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? "register-password-error" : undefined}
            required
          />
          {errors.password ? (
            <p className="field-error" id="register-password-error">
              {errors.password}
            </p>
          ) : null}
        </div>

        {formError ? (
          <p className="form-status error" role="alert">
            {formError}
          </p>
        ) : null}
        {successMessage ? (
          <p className="form-status success" role="status">
            {successMessage} {" "}
            <Link className="text-link" href="/login">
              Masuk
            </Link>
          </p>
        ) : null}

        <button className="button" type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
          {isSubmitting ? "Membuat akun..." : "Daftar"}
        </button>
      </form>

      <p className="muted">
        Sudah punya akun?{" "}
        <Link className="text-link" href="/login">
          Masuk
        </Link>
      </p>
    </>
  );
}
