"""Identitas user dari access token.

TODO(auth): PLACEHOLDER sampai modul auth dari anggota tim lain masuk ke repo.
Ganti `get_current_user_id` dengan dependency milik modul auth. Endpoint di modul
trip/chat hanya bergantung pada fungsi ini (mengembalikan user_id), jadi cukup
diganti di satu tempat.
"""

import uuid

import jwt
from fastapi import HTTPException, Request, status

from app.core.config import get_settings


def get_current_user_id(request: Request) -> uuid.UUID:
    settings = get_settings()

    # Utama: JWT di httpOnly cookie. Fallback: header Authorization Bearer (untuk Swagger/testing).
    token = request.cookies.get(settings.access_token_cookie_name)
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Belum login.")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token tidak valid atau kedaluwarsa.")
