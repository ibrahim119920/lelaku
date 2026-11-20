"""Helper kriptografi untuk modul auth: password (Argon2) dan token sesi opaque.

Argon2 sengaja lambat dan memakan CPU/memori. Kalau dipanggil langsung di `async def`
ia membekukan event loop dan semua request lain ikut menunggu, jadi hashing/verify
selalu dijalankan di thread terpisah (`asyncio.to_thread`). Library-nya melepas GIL
saat menghitung, jadi thread itu benar-benar berjalan paralel di core lain.
"""

import asyncio
import secrets
from hashlib import sha256

from pwdlib import PasswordHash

_password_hasher = PasswordHash.recommended()

# Hash palsu untuk membuat waktu respons login relatif sama baik email terdaftar atau tidak,
# sehingga tidak bisa dipakai menebak email mana yang punya akun.
_DUMMY_PASSWORD_HASH = _password_hasher.hash(secrets.token_urlsafe(32))


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_password_hasher.hash, password)


async def verify_password(password: str, password_hash: str | None) -> bool:
    """True hanya kalau password cocok. `password_hash=None` (user tidak ada) selalu False
    tapi tetap menjalankan satu verifikasi penuh agar waktunya sebanding."""
    try:
        if password_hash is None:
            await asyncio.to_thread(_password_hasher.verify, password, _DUMMY_PASSWORD_HASH)
            return False
        return await asyncio.to_thread(_password_hasher.verify, password, password_hash)
    except Exception:
        # Hash tersimpan rusak/tidak didukung: gagal tertutup tanpa membocorkan alasannya.
        return False


def generate_session_token() -> str:
    """Token opaque 256-bit untuk cookie. Nilai mentah hanya dikirim ke browser."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """SHA-256 hex dari token; hanya digest ini yang disimpan di database.

    SHA-256 cukup (tanpa salt/hash lambat) karena token berentropi tinggi, bukan password.
    """
    return sha256(token.encode("utf-8")).hexdigest()
