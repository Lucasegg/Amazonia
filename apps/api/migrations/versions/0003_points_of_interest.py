"""Create points of interest catalog."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_points_of_interest"
down_revision: Union[str, None] = "0002_character_hex_position"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "points_of_interest",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_ref", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("cell_q", sa.Integer(), nullable=False),
        sa.Column("cell_r", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("source_license", sa.String(length=40), nullable=False),
        sa.Column("source_url", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_ref", name="uq_poi_source_ref"),
    )
    op.create_index("ix_poi_cell", "points_of_interest", ["cell_q", "cell_r"])


def downgrade() -> None:
    op.drop_index("ix_poi_cell", table_name="points_of_interest")
    op.drop_table("points_of_interest")
