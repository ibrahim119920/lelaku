import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from backend.app.auth_routes import router as auth_router
from backend.app.database import (
    DatabaseConfigurationError,
    check_database_connection,
)
from backend.app.errors import ApiError


app = FastAPI(
    title="Lelaku API",
    description="Backend API Lelaku dengan PostgreSQL sebagai database utama.",
    version="0.1.0",
)

frontend_origin = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000").strip()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin.rstrip("/")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)

app.include_router(auth_router)


@app.exception_handler(ApiError)
async def api_error_handler(_request: Request, error: ApiError) -> JSONResponse:
    detail: dict[str, object] = {
        "code": error.code,
        "message": error.message,
    }
    if error.fields:
        detail["fields"] = error.fields
    return JSONResponse(
        status_code=error.status_code,
        content={"error": detail},
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    fields: dict[str, str] = {}
    for issue in error.errors():
        location = issue.get("loc", ())
        field = location[-1] if location else None
        if not isinstance(field, str):
            continue

        error_type = issue.get("type", "")
        is_login = request.url.path == "/auth/login"
        if field == "name":
            message = (
                "Nama wajib diisi."
                if error_type == "missing"
                else "Nama minimal terdiri dari 2 karakter."
            )
        elif field == "email":
            message = "Email wajib diisi." if error_type == "missing" else "Masukkan email yang valid."
        elif field == "phone":
            message = (
                "Nomor telepon wajib diisi."
                if error_type == "missing"
                else "Periksa kembali nomor telepon."
            )
        elif field == "password":
            if error_type == "missing" or (is_login and error_type == "string_too_short"):
                message = "Kata sandi wajib diisi."
            elif error_type == "string_too_long":
                message = "Kata sandi terlalu panjang."
            else:
                message = "Kata sandi minimal terdiri dari 8 karakter."
        else:
            continue
        fields[field] = message

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Periksa kembali input.",
                "fields": fields,
            }
        },
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(SQLAlchemyError)
@app.exception_handler(DatabaseConfigurationError)
async def database_error_handler(_request: Request, _error: Exception) -> JSONResponse:
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
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def database_health_check() -> dict[str, str]:
    try:
        check_database_connection()
    except (DatabaseConfigurationError, SQLAlchemyError, OSError) as error:
        # Do not return connection details or credentials to an HTTP client.
        raise HTTPException(
            status_code=503,
            detail="Database belum dapat dihubungi. Periksa konfigurasi backend.",
        ) from error

    return {"status": "ok", "database": "connected"}
