from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import InterfaceError, OperationalError

from app.auth.router import auth_router, profile_router
from app.chat.router import messages_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import ApiError, AppError, api_error_handler, app_error_handler
from app.trip.router import trips_router, users_router

app = FastAPI(title="Lelaku API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,  # cookie sesi dikirim lewat httpOnly cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(ApiError, api_error_handler)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(trips_router)
app.include_router(messages_router)
app.include_router(users_router)

# Pesan validasi yang ramah untuk form auth/profile (kontrak LL-05: error.fields per field).
_AUTH_PATHS = ("/auth/", "/profile")


def _field_message(field: str, error_type: str, *, is_login: bool) -> str | None:
    if field == "name":
        return "Nama wajib diisi." if error_type == "missing" else "Nama minimal terdiri dari 2 karakter."
    if field == "email":
        return "Email wajib diisi." if error_type == "missing" else "Masukkan email yang valid."
    if field == "phone":
        return "Nomor telepon wajib diisi." if error_type == "missing" else "Periksa kembali nomor telepon."
    if field == "password":
        if error_type == "missing" or (is_login and error_type == "string_too_short"):
            return "Kata sandi wajib diisi."
        if error_type == "string_too_long":
            return "Kata sandi terlalu panjang."
        return "Kata sandi minimal terdiri dari 8 karakter."
    return None


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError):
    # Endpoint trip/chat tetap memakai format bawaan FastAPI ({"detail": [...]}).
    if not request.url.path.startswith(_AUTH_PATHS):
        return await request_validation_exception_handler(request, error)

    is_login = request.url.path == "/auth/login"
    fields: dict[str, str] = {}
    for issue in error.errors():
        location = issue.get("loc", ())
        field = location[-1] if location else None
        if isinstance(field, str):
            message = _field_message(field, issue.get("type", ""), is_login=is_login)
            if message:
                fields[field] = message

    return JSONResponse(
        status_code=422,
        content={
            "error": {"code": "VALIDATION_ERROR", "message": "Periksa kembali input.", "fields": fields}
        },
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(OperationalError)
@app.exception_handler(InterfaceError)
async def database_unavailable_handler(_: Request, __: Exception):
    # Jangan bocorkan detail koneksi/credential; frontend membedakan 503 dari "belum login".
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Layanan sementara tidak tersedia. Coba lagi nanti.",
            }
        },
        headers={"Cache-Control": "no-store"},
    )


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
async def health_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="Database belum dapat dihubungi. Periksa konfigurasi backend."
        ) from error
    return {"status": "ok", "database": "connected"}
