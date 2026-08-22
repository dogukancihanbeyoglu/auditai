"""add explainable risk scores

Revision ID: 6f9f18d41e75
Revises: 93037f1b9bbe
"""
from alembic import op
import sqlalchemy as sa


revision = "6f9f18d41e75"
down_revision = "93037f1b9bbe"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "risk_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("audit_area_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("alarm_count", sa.Integer(), nullable=False),
        sa.Column("open_alarm_count", sa.Integer(), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["audit_area_id"], ["audit_areas.id"]),
        sa.ForeignKeyConstraint(["rule_id"], ["audit_rules.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_scores_rule_id", "risk_scores", ["rule_id"])
    op.create_index("ix_risk_scores_audit_area_id", "risk_scores", ["audit_area_id"])
    op.create_index("ix_risk_scores_calculated_at", "risk_scores", ["calculated_at"])


def downgrade():
    op.drop_index("ix_risk_scores_calculated_at", table_name="risk_scores")
    op.drop_index("ix_risk_scores_audit_area_id", table_name="risk_scores")
    op.drop_index("ix_risk_scores_rule_id", table_name="risk_scores")
    op.drop_table("risk_scores")
