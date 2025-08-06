from sqlmodel import create_engine, SQLModel, Session as SQLSession
from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with SQLSession(engine) as session:
        yield session