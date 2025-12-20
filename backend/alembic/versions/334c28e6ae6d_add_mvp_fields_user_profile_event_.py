"""Add MVP fields: user profile, event details, applications

Revision ID: 334c28e6ae6d
Revises:
Create Date: 2025-12-20 11:56:28.649604

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "334c28e6ae6d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Добавляем поля в таблицу users
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("sports", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("note", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))

    # Добавляем поля в таблицу events
    op.add_column("events", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("events", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("events", sa.Column("sport_type", sa.String(length=100), nullable=True))
    op.add_column("events", sa.Column("max_participants", sa.Integer(), nullable=True))
    op.add_column("events", sa.Column("fee", sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column("events", sa.Column("note", sa.Text(), nullable=True))

    # Создаём индекс для sport_type для быстрого поиска
    op.create_index(op.f("ix_events_sport_type"), "events", ["sport_type"], unique=False)

    # Создаём таблицу event_applications
    op.create_table(
        "event_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_event_applications_user_id"), "event_applications", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_event_applications_event_id"), "event_applications", ["event_id"], unique=False
    )
    op.create_index(
        op.f("ix_event_applications_status"), "event_applications", ["status"], unique=False
    )


def downgrade() -> None:
    # Удаляем таблицу event_applications
    op.drop_index(op.f("ix_event_applications_status"), table_name="event_applications")
    op.drop_index(op.f("ix_event_applications_event_id"), table_name="event_applications")
    op.drop_index(op.f("ix_event_applications_user_id"), table_name="event_applications")
    op.drop_table("event_applications")

    # Удаляем индекс и поля из events
    op.drop_index(op.f("ix_events_sport_type"), table_name="events")
    op.drop_column("events", "note")
    op.drop_column("events", "fee")
    op.drop_column("events", "max_participants")
    op.drop_column("events", "sport_type")
    op.drop_column("events", "longitude")
    op.drop_column("events", "latitude")

    # Удаляем поля из users
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "note")
    op.drop_column("users", "sports")
    op.drop_column("users", "city")
    op.drop_column("users", "gender")
    op.drop_column("users", "age")
