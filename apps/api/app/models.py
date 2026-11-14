"""Entidades SQLAlchemy para campanhas."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Campaign(Base):
    """Campanha individual e ficha inicial de seu personagem."""
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    character_name: Mapped[str] = mapped_column(String(60), nullable=False)
    profession: Mapped[str] = mapped_column(String(30), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False)
    skills: Mapped[dict] = mapped_column(JSON, nullable=False)
    health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    hunger: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thirst: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fatigue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
