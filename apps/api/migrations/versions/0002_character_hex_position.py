"""Add persisted hex position and discovered cells to characters."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_character_hex_position"
down_revision: Union[str, None] = "0001_campaigns_characters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("position_q", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "characters",
        sa.Column("position_r", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "characters",
        sa.Column(
            "discovered_cells",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("""'["0:0"]'"""),
        ),
    )


def downgrade() -> None:
    op.drop_column("characters", "discovered_cells")
    op.drop_column("characters", "position_r")
    op.drop_column("characters", "position_q")
