"""Add persistent auth throttling and revocable session versions."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005_auth_hardening"
down_revision: Union[str, None] = "0004_user_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("session_version", sa.Integer(), server_default="0", nullable=False))
    op.create_table(
        "auth_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scope", sa.String(length=24), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_attempts_scope_key_time", "auth_attempts", ["scope", "key_hash", "attempted_at"])

def downgrade() -> None:
    op.drop_index("ix_auth_attempts_scope_key_time", table_name="auth_attempts")
    op.drop_table("auth_attempts")
    op.drop_column("users", "session_version")
