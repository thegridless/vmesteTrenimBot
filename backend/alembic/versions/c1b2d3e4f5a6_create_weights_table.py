"""Create weights table

Revision ID: c1b2d3e4f5a6
Revises: 8f2c9d1a4b6e
Create Date: 2026-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1b2d3e4f5a6"
down_revision: Union[str, None] = "8f2c9d1a4b6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("exercise", sa.String(length=255), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weight", sa.Numeric(10, 2), nullable=False),
    )
    op.create_index("ix_weights_user_id", "weights", ["user_id"])
    op.create_index("ix_weights_exercise", "weights", ["exercise"])


def downgrade() -> None:
    op.drop_index("ix_weights_exercise", table_name="weights")
    op.drop_index("ix_weights_user_id", table_name="weights")
    op.drop_table("weights")
