from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str = Field(min_length=4, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    name: str
    email: EmailStr
    phone: str | None
    profile_photo: str | None
    identity_status: Literal["verified", "unverified"]
    avg_rating: float | None
    total_ratings: int
    total_trips_completed: int


class UserDataEnvelope(BaseModel):
    data: PublicUser
