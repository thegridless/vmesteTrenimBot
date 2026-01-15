"""add_sports_table_and_relations

Revision ID: 3a4c76ef5873
Revises: 334c28e6ae6d
Create Date: 2026-01-15 08:08:39.866678

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a4c76ef5873"
down_revision: str | None = "334c28e6ae6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Миграция для добавления таблицы sports и связей с users и events.
    """
    # 1. Создаем таблицу sports
    op.create_table(
        "sports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sports_id"), "sports", ["id"], unique=False)
    op.create_index(op.f("ix_sports_name"), "sports", ["name"], unique=True)

    # 2. Создаем промежуточную таблицу user_sports
    op.create_table(
        "user_sports",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sport_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "sport_id"),
    )

    # 3. Добавляем колонку sport_id в events
    op.add_column("events", sa.Column("sport_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_events_sport_id"), "events", ["sport_id"], unique=False)
    op.create_foreign_key(
        "fk_events_sport_id", "events", "sports", ["sport_id"], ["id"], ondelete="SET NULL"
    )

    # 4. Заполняем таблицу sports стандартными видами спорта
    op.execute("""
        INSERT INTO sports (name, active) VALUES
        ('Футбол', true),
        ('Баскетбол', true),
        ('Волейбол', true),
        ('Теннис', true),
        ('Бег', true),
        ('Йога', true),
        ('Плавание', true),
        ('Велоспорт', true),
        ('Тренажёрный зал', true),
        ('Бокс', true)
    """)

    # 5. Мигрируем данные из sport_type в sport_id для events
    # Связываем события с видами спорта по названию
    op.execute("""
        UPDATE events
        SET sport_id = (SELECT id FROM sports WHERE sports.name = events.sport_type)
        WHERE sport_type IS NOT NULL
    """)

    # 6. Удаляем старую колонку sport_type
    op.drop_index("ix_events_sport_type", table_name="events")
    op.drop_column("events", "sport_type")

    # 7. Удаляем старую колонку sports из users (JSON)
    op.drop_column("users", "sports")


def downgrade() -> None:
    """
    Откат миграции.
    """
    # 1. Восстанавливаем колонку sports в users
    op.add_column("users", sa.Column("sports", sa.JSON(), nullable=True))

    # 2. Восстанавливаем колонку sport_type в events
    op.add_column("events", sa.Column("sport_type", sa.String(100), nullable=True))
    op.create_index("ix_events_sport_type", "events", ["sport_type"], unique=False)

    # 3. Мигрируем данные обратно из sport_id в sport_type
    op.execute("""
        UPDATE events
        SET sport_type = (SELECT name FROM sports WHERE sports.id = events.sport_id)
        WHERE sport_id IS NOT NULL
    """)

    # 4. Удаляем внешний ключ и колонку sport_id
    op.drop_constraint("fk_events_sport_id", "events", type_="foreignkey")
    op.drop_index(op.f("ix_events_sport_id"), table_name="events")
    op.drop_column("events", "sport_id")

    # 5. Удаляем таблицу user_sports
    op.drop_table("user_sports")

    # 6. Удаляем таблицу sports
    op.drop_index(op.f("ix_sports_name"), table_name="sports")
    op.drop_index(op.f("ix_sports_id"), table_name="sports")
    op.drop_table("sports")
