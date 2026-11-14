"""Cria tabela de campanhas."""
from alembic import op
import sqlalchemy as sa

revision = "0001_create_campaigns"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Cria a tabela inicial com estado do personagem."""
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("character_name", sa.String(60), nullable=False),
        sa.Column("profession", sa.String(30), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("starting_items", sa.JSON(), nullable=False),
        sa.Column("contextual_strength", sa.String(240), nullable=False),
        sa.Column("health", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("hunger", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("thirst", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fatigue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

def downgrade() -> None:
    """Remove a tabela criada por esta migração."""
    op.drop_table("campaigns")
