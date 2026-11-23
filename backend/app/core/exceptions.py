from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Error domain yang dilempar service layer, dipetakan ke HTTP response di main."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


class ApiError(Exception):
    """Error dengan kode yang stabil untuk modul auth/profile.

    Dipetakan ke `{"error": {"code", "message", "fields"?}}` (kontrak LL-05), berbeda dari
    AppError yang memakai `{"detail": ...}`. `message` harus aman ditampilkan ke pengguna.
    """

    def __init__(self, status_code: int, code: str, message: str, fields: dict[str, str] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    error: dict[str, object] = {"code": exc.code, "message": exc.message}
    if exc.fields:
        error["fields"] = exc.fields
    return JSONResponse(
        status_code=exc.status_code, content={"error": error}, headers={"Cache-Control": "no-store"}
    )
