"""Seed sports table from SportType enum

Revision ID: 8f2c9d1a4b6e
Revises: ba1e431dd0fc
Create Date: 2026-01-29 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f2c9d1a4b6e"
down_revision: Union[str, None] = "ba1e431dd0fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SPORT_NAMES = [
    "Футбол",
    "Баскетбол",
    "Волейбол",
    "Теннис",
    "Бег",
    "Йога",
    "Плавание",
    "Велоспорт",
    "Тренажёрный зал",
    "Бокс",
]


def upgrade() -> None:
    sports_table = sa.table(
        "sports",
        sa.column("name", sa.String()),
        sa.column("active", sa.Boolean()),
    )
    op.bulk_insert(
        sports_table,
        [{"name": name, "active": True} for name in SPORT_NAMES],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM sports WHERE name IN :names",
        ).bindparams(sa.bindparam("names", expanding=True)),
        {"names": SPORT_NAMES},
    )
