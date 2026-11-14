"""Adiciona posição, locais descobertos e eventos idempotentes."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_world_exploration"
down_revision: Union[str, None] = "0001_campaigns_characters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona estado geográfico ao personagem e trilha de ações."""
    op.add_column(
        "characters",
        sa.Column(
            "position",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("""'{"location_id":"praca_se","latitude":-23.55037,"longitude":-46.63395}'"""),
        ),
    )
    op.add_column(
        "characters",
        sa.Column(
            "discovered_locations",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("""'["praca_se"]'"""),
        ),
    )
    op.create_table(
        "world_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(length=36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "character_id",
            sa.String(length=36),
            sa.ForeignKey("characters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("world_time_minutes", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "campaign_id", "idempotency_key", name="uq_world_events_campaign_idempotency"
        ),
    )
    op.create_index("ix_world_events_campaign_id", "world_events", ["campaign_id"])
    op.create_index("ix_world_events_character_id", "world_events", ["character_id"])


def downgrade() -> None:
    """Remove a trilha de eventos e os campos geográficos adicionados."""
    op.drop_index("ix_world_events_character_id", table_name="world_events")
    op.drop_index("ix_world_events_campaign_id", table_name="world_events")
    op.drop_table("world_events")
    op.drop_column("characters", "discovered_locations")
    op.drop_column("characters", "position")
