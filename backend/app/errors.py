from dataclasses import dataclass


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    fields: dict[str, str] | None = None

    def __str__(self) -> str:
        return self.message
