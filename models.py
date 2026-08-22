"""Core persistence models for the AuditAI prototype."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditArea(db.Model):
    __tablename__ = "audit_areas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False, default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    data_sources = db.relationship("DataSource", back_populates="audit_area", cascade="all, delete-orphan")
    rules = db.relationship("AuditRule", back_populates="audit_area", cascade="all, delete-orphan")
    alarms = db.relationship("Alarm", back_populates="audit_area", cascade="all, delete-orphan")


class DataSource(db.Model):
    __tablename__ = "data_sources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    source_type = db.Column(db.String(32), nullable=False, default="synthetic")
    config = db.Column(db.JSON, nullable=False, default=dict)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_sync = db.Column(db.DateTime(timezone=True), nullable=True)
    audit_area_id = db.Column(db.Integer, db.ForeignKey("audit_areas.id"), nullable=False)

    audit_area = db.relationship("AuditArea", back_populates="data_sources")
    rules = db.relationship("AuditRule", back_populates="data_source")
    alarms = db.relationship("Alarm", back_populates="data_source")


class AuditRule(db.Model):
    __tablename__ = "audit_rules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    field_name = db.Column(db.String(64), nullable=False)
    operator = db.Column(db.String(8), nullable=False, default=">")
    threshold_value = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(16), nullable=False, default="medium")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_run_at = db.Column(db.DateTime(timezone=True), nullable=True)
    trigger_count = db.Column(db.Integer, nullable=False, default=0)
    audit_area_id = db.Column(db.Integer, db.ForeignKey("audit_areas.id"), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False)

    audit_area = db.relationship("AuditArea", back_populates="rules")
    data_source = db.relationship("DataSource", back_populates="rules")
    alarms = db.relationship("Alarm", back_populates="rule", cascade="all, delete-orphan")


class Alarm(db.Model):
    __tablename__ = "alarms"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="open")
    affected_records = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    audit_area_id = db.Column(db.Integer, db.ForeignKey("audit_areas.id"), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey("audit_rules.id"), nullable=False)

    audit_area = db.relationship("AuditArea", back_populates="alarms")
    data_source = db.relationship("DataSource", back_populates="alarms")
    rule = db.relationship("AuditRule", back_populates="alarms")
