"""Create user accounts and assign campaign ownership."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_user_accounts"
down_revision: Union[str, None] = "0003_points_of_interest"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    with op.batch_alter_table("campaigns", recreate="auto") as batch:
        batch.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))
        batch.create_foreign_key(
            "fk_campaigns_user_id_users", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )
    op.create_index("ix_campaigns_user_id", "campaigns", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_campaigns_user_id", table_name="campaigns")
    with op.batch_alter_table("campaigns", recreate="auto") as batch:
        batch.drop_constraint("fk_campaigns_user_id_users", type_="foreignkey")
        batch.drop_column("user_id")
    op.drop_table("users")
