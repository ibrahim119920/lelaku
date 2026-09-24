from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.database import get_database_engine


def get_database_session() -> Generator[Session, None, None]:
    with Session(get_database_engine()) as session:
        yield session
