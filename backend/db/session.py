from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

DB_URL = settings.DATABASE_URL

connect_args = {}
if DB_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DB_URL, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
