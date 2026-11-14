"""Add cosmetic appearance configuration to characters."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007_character_appearance"
down_revision: Union[str, None] = "0006_account_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("characters", sa.Column("appearance", sa.JSON(), nullable=True))
    op.execute("UPDATE characters SET appearance = '{}' WHERE appearance IS NULL")
    with op.batch_alter_table("characters") as batch:
        batch.alter_column("appearance", existing_type=sa.JSON(), nullable=False)

def downgrade() -> None:
    op.drop_column("appearance")