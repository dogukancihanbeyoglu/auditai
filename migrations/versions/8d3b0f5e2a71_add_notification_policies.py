"""add notification policies

Revision ID: 8d3b0f5e2a71
Revises: 7c2a9e4d1f60
"""

from alembic import op
import sqlalchemy as sa


revision = "8d3b0f5e2a71"
down_revision = "7c2a9e4d1f60"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("severity", "channel", "recipient", name="uq_notification_policy_route"),
    )


def downgrade():
    op.drop_table("notification_policies")
