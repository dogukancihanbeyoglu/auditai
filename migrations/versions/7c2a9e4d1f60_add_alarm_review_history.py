"""add alarm review history

Revision ID: 7c2a9e4d1f60
Revises: 1a7d4e2b3c90
"""

from alembic import op
import sqlalchemy as sa


revision = "7c2a9e4d1f60"
down_revision = "1a7d4e2b3c90"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alarm_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alarm_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("from_value", sa.String(length=255), nullable=True),
        sa.Column("to_value", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["alarm_id"], ["alarms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, column in (("ix_alarm_activities_alarm_id", "alarm_id"),
                         ("ix_alarm_activities_actor_id", "actor_id"),
                         ("ix_alarm_activities_event_type", "event_type"),
                         ("ix_alarm_activities_created_at", "created_at")):
        op.create_index(name, "alarm_activities", [column], unique=False)


def downgrade():
    op.drop_table("alarm_activities")
