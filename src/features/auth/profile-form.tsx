"use client";

import { type FormEvent, useState } from "react";

import {
  AuthApiError,
  getAuthErrorMessage,
  requestAuthApi,
} from "@/lib/auth/client";
import { parseUserProfile, type UserProfile } from "@/lib/auth/types";

type ProfileFormProps = {
  initialProfile: UserProfile;
};

type ProfileErrors = {
  name?: string;
  phone?: string;
};

function validateProfile(name: string, phone: string): ProfileErrors {
  const errors: ProfileErrors = {};

  if (name.trim().length < 2) {
    errors.name = "Nama minimal terdiri dari 2 karakter.";
  }

  if (!phone.trim()) {
    errors.phone = "Nomor telepon wajib diisi.";
  }

  return errors;
}

export default function ProfileForm({ initialProfile }: ProfileFormProps) {
  const [profile, setProfile] = useState(initialProfile);
  const [name, setName] = useState(initialProfile.name);
  const [phone, setPhone] = useState(initialProfile.phone ?? "");
  const [errors, setErrors] = useState<ProfileErrors>({});
  const [formMessage, setFormMessage] = useState("");
  const [formError, setFormError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormMessage("");
    setFormError("");

    const validationErrors = validateProfile(name, phone);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSaving(true);

    try {
      const response = await requestAuthApi<unknown>("/profile", {
        method: "PATCH",
        body: JSON.stringify({ name: name.trim(), phone: phone.trim() }),
      });
      const updatedProfile = parseUserProfile(response);

      if (!updatedProfile) {
        throw new Error("Response profile tidak valid.");
      }

      setProfile(updatedProfile);
      setName(updatedProfile.name);
      setPhone(updatedProfile.phone ?? "");
      setFormMessage("Profil berhasil disimpan.");
    } catch (error) {
      if (error instanceof AuthApiError) {
        setErrors({ name: error.fields.name, phone: error.fields.phone });
      }
      setFormError(getAuthErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogout() {
    setFormMessage("");
    setFormError("");
    setIsLoggingOut(true);

    try {
      await requestAuthApi("/auth/logout", { method: "POST" });
      window.location.replace("/login");
    } catch (error) {
      setFormError(getAuthErrorMessage(error));
      setIsLoggingOut(false);
    }
  }

  return (
    <div className="stack">
      <div className="profile-summary">
        <div className="profile-photo" aria-hidden={profile.profile_photo ? undefined : true}>
          {profile.profile_photo ? (
            // The backend supplies the already-authorized profile photo URL.
            <img src={profile.profile_photo} alt={`Foto profil ${profile.name}`} />
          ) : (
            <span aria-hidden="true">{profile.name.slice(0, 1).toUpperCase()}</span>
          )}
        </div>
        <dl className="profile-details">
          <div>
            <dt>Email</dt>
            <dd>{profile.email}</dd>
          </div>
          <div>
            <dt>Status identitas</dt>
            <dd>
              <span className={`status-badge ${profile.identity_status}`}>
                {profile.identity_status === "verified" ? "Terverifikasi" : "Belum terverifikasi"}
              </span>
            </dd>
          </div>
        </dl>
      </div>

      <form className="form-grid" onSubmit={handleSave} noValidate>
        <div className="field">
          <label htmlFor="profile-name">Nama</label>
          <input
            id="profile-name"
            name="name"
            type="text"
            autoComplete="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "profile-name-error" : undefined}
            required
          />
          {errors.name ? (
            <p className="field-error" id="profile-name-error">
              {errors.name}
            </p>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="profile-phone">Nomor telepon</label>
          <input
            id="profile-phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            inputMode="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            aria-invalid={Boolean(errors.phone)}
            aria-describedby={errors.phone ? "profile-phone-error" : undefined}
            required
          />
          {errors.phone ? (
            <p className="field-error" id="profile-phone-error">
              {errors.phone}
            </p>
          ) : null}
        </div>

        {formError ? (
          <p className="form-status error" role="alert">
            {formError}
          </p>
        ) : null}
        {formMessage ? (
          <p className="form-status success" role="status">
            {formMessage}
          </p>
        ) : null}

        <div className="actions">
          <button className="button" type="submit" disabled={isSaving || isLoggingOut} aria-busy={isSaving}>
            {isSaving ? "Menyimpan..." : "Simpan perubahan"}
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={handleLogout}
            disabled={isSaving || isLoggingOut}
            aria-busy={isLoggingOut}
          >
            {isLoggingOut ? "Keluar..." : "Logout"}
          </button>
        </div>
      </form>
    </div>
  );
}
