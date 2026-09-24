import uuid

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class UUIDText(TypeDecorator[uuid.UUID]):
    """Expose UUIDs in Python while keeping the existing LL-05 TEXT columns."""

    impl = Text
    cache_ok = True

    @property
    def python_type(self) -> type[uuid.UUID]:
        return uuid.UUID

    def process_bind_param(self, value: uuid.UUID | str | None, _dialect):
        if value is None:
            return None
        return str(value if isinstance(value, uuid.UUID) else uuid.UUID(value))

    def process_result_value(self, value: str | None, _dialect):
        return uuid.UUID(value) if value is not None else None


class Base(DeclarativeBase):
    pass
