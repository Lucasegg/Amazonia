"""Conexão SQLAlchemy usando a URL do ambiente configurado."""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Classe-base de todos os modelos persistidos."""


def _build_engine():
    """Cria engine e exige DATABASE_URL para evitar banco implícito acidental."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL precisa apontar para o banco do ambiente.")
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão por requisição e garante seu fechamento."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
