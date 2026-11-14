"""Modelos persistidos de usuários, campanhas, personagens e pontos de interesse."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def utc_now() -> datetime:
    """Retorna instante UTC para auditoria dos registros."""
    return datetime.now(timezone.utc)

class User(Base):
    """Conta autenticável proprietária de campanhas."""
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    session_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    role: Mapped[str] = mapped_column(String(24), nullable=False, default="player", server_default="player")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class AuthAttempt(Base):
    """Armazena identificadores irreversíveis para limitação persistente de tentativas."""
    __tablename__ = "auth_attempts"
    __table_args__ = (Index("ix_auth_attempts_scope_key_time", "scope", "key_hash", "attempted_at"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(24), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

class AccountToken(Base):
    """Token de uso único para verificação de e-mail e recuperação de senha."""
    __tablename__ = "account_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_account_tokens_token_hash"),
        Index("ix_account_tokens_user_purpose", "user_id", "purpose"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(24), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    world_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    user: Mapped["User | None"] = relationship(back_populates="campaigns")
    character: Mapped["Character | None"] = relationship(back_populates="campaign", cascade="all, delete-orphan", uselist=False)

class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("campaign_id", name="uq_characters_campaign_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    origin: Mapped[str] = mapped_column(String(40), nullable=False)
    attributes: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    skills: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    inventory: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    needs: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=lambda: {"hunger": 0, "thirst": 0, "fatigue": 0, "health": 100})
    position_q: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position_r: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discovered_cells: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: ["0:0"])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    campaign: Mapped[Campaign] = relationship(back_populates="character")

class PointOfInterest(Base):
    __tablename__ = "points_of_interest"
    __table_args__ = (UniqueConstraint("source_ref", name="uq_poi_source_ref"), Index("ix_poi_cell", "cell_q", "cell_r"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    cell_q: Mapped[int] = mapped_column(Integer, nullable=False)
    cell_r: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    source_license: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
