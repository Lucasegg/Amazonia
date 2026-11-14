"""Modelos persistidos da campanha, personagem e eventos do mundo."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Retorna horário UTC para trilhas de auditoria."""
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    world_time_minutes: Mapped[int] = mapped_column(nullable=False, default=0)
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
    position: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False,
        default=lambda: {"location_id": "praca_se", "latitude": -23.55037, "longitude": -46.63395},
    )
    discovered_locations: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=lambda: ["praca_se"]
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    campaign: Mapped[Campaign] = relationship(back_populates="character")


class WorldEvent(Base):
    """Evento imutável de exploração com chave de idempotência por campanha."""

    __tablename__ = "world_events"
    __table_args__ = (
        UniqueConstraint("campaign_id", "idempotency_key", name="uq_world_events_campaign_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(24), nullable=False)
    world_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
