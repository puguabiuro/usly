# -*- coding: utf-8 -*-

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# Plik SQLite będzie utworzony w folderze backend/ jako: usly.db
DATABASE_URL = "sqlite:///./backend/usly.db"


class Base(DeclarativeBase):
    pass


# check_same_thread=False jest wymagane dla SQLite przy FastAPI (wielowątkowość)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
def init_db() -> None:
    # Import modeli tutaj, żeby SQLAlchemy je „zobaczyło”
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
# --- Dependency: DB session (FastAPI Depends) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# === HOTFIX: stała ścieżka do SQLite w backend/usly.db + get_db ===
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# jeśli Base nie istnieje w tym pliku, utwórz (bezpiecznie)
try:
    Base  # type: ignore[name-defined]
except NameError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()

# db/database.py jest w: backend/db/database.py
# więc backend/ to: parents[1]
DB_PATH = Path(__file__).resolve().parents[1] / "usly.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
