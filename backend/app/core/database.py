from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    pass


engine_kwargs = {"future": True}
if settings.postgres_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(settings.postgres_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
