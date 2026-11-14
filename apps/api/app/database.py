"""Conexão SQLAlchemy e dependência de sessão."""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.config import get_settings

class Base(DeclarativeBase):
    """Classe-base dos modelos persistidos."""

def build_engine(database_url: str | None = None):
    """Cria engine usando URL explícita ou configuração do ambiente."""
    url = database_url or get_settings().database_url
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=args)

engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão por requisição e fecha ao final."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
