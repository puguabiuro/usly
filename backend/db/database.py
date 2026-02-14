# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.engine import Engine


class Base(DeclarativeBase):
    pass


def _default_sqlite_url() -> str:
    # backend/db/database.py -> backend/ is parents[1]
    db_path = Path(__file__).resolve().parents[1] / "usly.db"
    return f"sqlite:///{db_path.as_posix()}"


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    return url or _default_sqlite_url()


def make_engine(url: str) -> Engine:
    # SQLite needs check_same_thread=False; Postgres does not.
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


DATABASE_URL = get_database_url()
engine = make_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
