from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat.router import messages_router
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.trip.router import trips_router, users_router

app = FastAPI(title="Lelaku API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,  # access token dikirim lewat httpOnly cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)

app.include_router(trips_router)
app.include_router(messages_router)
app.include_router(users_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
