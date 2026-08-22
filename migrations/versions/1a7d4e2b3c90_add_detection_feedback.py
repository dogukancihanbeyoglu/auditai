"""add detection feedback

Revision ID: 1a7d4e2b3c90
Revises: 229ebea0961f
"""
from alembic import op
import sqlalchemy as sa


revision = "1a7d4e2b3c90"
down_revision = "229ebea0961f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "detection_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alarm_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alarm_id"], ["alarms.id"]),
        sa.ForeignKeyConstraint(["rule_id"], ["audit_rules.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alarm_id", "user_id", name="uq_feedback_alarm_user"),
    )
    op.create_index(op.f("ix_detection_feedback_alarm_id"), "detection_feedback", ["alarm_id"])
    op.create_index(op.f("ix_detection_feedback_rule_id"), "detection_feedback", ["rule_id"])
    op.create_index(op.f("ix_detection_feedback_user_id"), "detection_feedback", ["user_id"])


def downgrade():
    op.drop_index(op.f("ix_detection_feedback_user_id"), table_name="detection_feedback")
    op.drop_index(op.f("ix_detection_feedback_rule_id"), table_name="detection_feedback")
    op.drop_index(op.f("ix_detection_feedback_alarm_id"), table_name="detection_feedback")
    op.drop_table("detection_feedback")
