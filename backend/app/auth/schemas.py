import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_PHONE_FORMAT = re.compile(r"\+?[0-9][0-9 ().-]*")


def _validate_phone_number(value: str) -> str:
    digit_count = sum(character.isascii() and character.isdigit() for character in value)
    if not _PHONE_FORMAT.fullmatch(value) or not 7 <= digit_count <= 15:
        raise ValueError("Nomor telepon tidak valid.")
    return value


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

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_phone_number(value)

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


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=4, max_length=32)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_phone_number(value)


class PublicUser(BaseModel):
    """DTO publik. Sengaja tidak memuat password_hash atau apa pun dari sesi."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    # `str` (bukan EmailStr) di sisi output: data sudah tervalidasi saat register, dan validasi
    # ulang bisa menolak email lama yang valid menurut kita tapi "special-use" menurut library.
    email: str
    phone: str | None
    profile_photo: str | None
    identity_status: str
    avg_rating: float | None
    total_ratings: int
    total_trips_completed: int


class UserDataEnvelope(BaseModel):
    data: PublicUser
