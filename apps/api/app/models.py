"""Modelos persistidos da campanha e personagem."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Retorna instante UTC para auditoria dos registros."""
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    world_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    character: Mapped["Character | None"] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", uselist=False
    )


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("campaign_id", name="uq_characters_campaign_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    origin: Mapped[str] = mapped_column(String(40), nullable=False)
    attributes: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    skills: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    inventory: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    needs: Mapped[dict[str, int]] = mapped_column(
        JSON, nullable=False, default=lambda: {"hunger": 0, "thirst": 0, "fatigue": 0, "health": 100}
    )
    position_q: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position_r: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discovered_cells: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: ["0:0"])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    campaign: Mapped[Campaign] = relationship(back_populates="character")
