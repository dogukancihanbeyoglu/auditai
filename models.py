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
    risk_scores = db.relationship("RiskScore", back_populates="audit_area", cascade="all, delete-orphan")


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
    field_mappings = db.relationship("FieldMapping", back_populates="data_source",
                                     cascade="all, delete-orphan")
    quality_checks = db.relationship("QualityCheck", back_populates="data_source",
                                     cascade="all, delete-orphan")
    sync_policy = db.relationship("DataSourceSyncPolicy", back_populates="data_source",
                                  cascade="all, delete-orphan", uselist=False)
    sync_runs = db.relationship("DataSourceSyncRun", back_populates="data_source",
                                cascade="all, delete-orphan")
    snapshots = db.relationship("DataSnapshot", back_populates="data_source",
                                cascade="all, delete-orphan")


class DataSourceSyncPolicy(db.Model):
    """Full-refresh policy and short-lived source lock."""

    __tablename__ = "data_source_sync_policies"

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False,
                               unique=True, index=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    refresh_mode = db.Column(db.String(16), nullable=False, default="full")
    max_records = db.Column(db.Integer, nullable=False, default=10_000)
    lock_token = db.Column(db.String(36), nullable=True)
    lock_until = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    data_source = db.relationship("DataSource", back_populates="sync_policy")


class DataSnapshot(db.Model):
    """Immutable metadata describing an activated source snapshot."""

    __tablename__ = "data_snapshots"
    __table_args__ = (db.UniqueConstraint("data_source_id", "version",
                                         name="uq_data_snapshot_source_version"),)

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="active")
    row_count = db.Column(db.Integer, nullable=False)
    schema_json = db.Column(db.JSON, nullable=False, default=list)
    content_checksum = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    activated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    data_source = db.relationship("DataSource", back_populates="snapshots")
    sync_runs = db.relationship("DataSourceSyncRun", back_populates="snapshot")


class DataSourceSyncRun(db.Model):
    """Persistent evidence for one idempotent source refresh attempt."""

    __tablename__ = "data_source_sync_runs"
    __table_args__ = (db.UniqueConstraint("data_source_id", "idempotency_key",
                                         name="uq_source_sync_idempotency"),)

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False, index=True)
    snapshot_id = db.Column(db.Integer, db.ForeignKey("data_snapshots.id"), nullable=True)
    idempotency_key = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="running")
    records_fetched = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    data_source = db.relationship("DataSource", back_populates="sync_runs")
    snapshot = db.relationship("DataSnapshot", back_populates="sync_runs")


class FieldMapping(db.Model):
    """Maps a discovered source column to a stable audit-domain field."""

    __tablename__ = "field_mappings"
    __table_args__ = (db.UniqueConstraint("data_source_id", "source_column", "target_field",
                                         name="uq_field_mapping_source_target"),)

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False, index=True)
    source_column = db.Column(db.String(128), nullable=False)
    target_field = db.Column(db.String(128), nullable=False)
    target_type = db.Column(db.String(24), nullable=False, default="string")
    transformation = db.Column(db.String(24), nullable=False, default="none")
    is_required = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    data_source = db.relationship("DataSource", back_populates="field_mappings")


class QualityCheck(db.Model):
    """Reusable quality assertion evaluated against persisted source records."""

    __tablename__ = "quality_checks"
    __table_args__ = (db.UniqueConstraint("data_source_id", "name", name="uq_quality_check_source_name"),)

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    check_type = db.Column(db.String(32), nullable=False)
    field_name = db.Column(db.String(128), nullable=False)
    parameters = db.Column(db.JSON, nullable=False, default=dict)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_run_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    data_source = db.relationship("DataSource", back_populates="quality_checks")
    runs = db.relationship("QualityCheckRun", back_populates="quality_check",
                           cascade="all, delete-orphan")


class QualityCheckRun(db.Model):
    """Immutable evidence from one data-quality execution."""

    __tablename__ = "quality_check_runs"

    id = db.Column(db.Integer, primary_key=True)
    quality_check_id = db.Column(db.Integer, db.ForeignKey("quality_checks.id"), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False)
    scanned_records = db.Column(db.Integer, nullable=False, default=0)
    failed_records = db.Column(db.Integer, nullable=False, default=0)
    pass_rate = db.Column(db.Float, nullable=False, default=0.0)
    failure_sample = db.Column(db.JSON, nullable=False, default=list)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    quality_check = db.relationship("QualityCheck", back_populates="runs")


class AuditRule(db.Model):
    __tablename__ = "audit_rules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    field_name = db.Column(db.String(64), nullable=False)
    operator = db.Column(db.String(8), nullable=False, default=">")
    threshold_value = db.Column(db.Float, nullable=False)
    rule_type = db.Column(db.String(24), nullable=False, default="numeric")
    parameters = db.Column(db.JSON, nullable=False, default=dict)
    schedule_interval_minutes = db.Column(db.Integer, nullable=True)
    next_run_at = db.Column(db.DateTime(timezone=True), nullable=True)
    schedule_enabled = db.Column(db.Boolean, nullable=False, default=True)
    execution_timeout_seconds = db.Column(db.Integer, nullable=False, default=300)
    schedule_retry_limit = db.Column(db.Integer, nullable=False, default=2)
    retry_delay_minutes = db.Column(db.Integer, nullable=False, default=5)
    consecutive_failures = db.Column(db.Integer, nullable=False, default=0)
    execution_lock_token = db.Column(db.String(36), nullable=True)
    execution_lock_until = db.Column(db.DateTime(timezone=True), nullable=True)
    severity = db.Column(db.String(16), nullable=False, default="medium")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_run_at = db.Column(db.DateTime(timezone=True), nullable=True)
    trigger_count = db.Column(db.Integer, nullable=False, default=0)
    audit_area_id = db.Column(db.Integer, db.ForeignKey("audit_areas.id"), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False)

    audit_area = db.relationship("AuditArea", back_populates="rules")
    data_source = db.relationship("DataSource", back_populates="rules")
    alarms = db.relationship("Alarm", back_populates="rule", cascade="all, delete-orphan")
    executions = db.relationship("RuleExecution", back_populates="rule", cascade="all, delete-orphan")
    risk_scores = db.relationship("RiskScore", back_populates="rule", cascade="all, delete-orphan")


class RuleExecution(db.Model):
    """Immutable evidence about one rule evaluation."""

    __tablename__ = "rule_executions"

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("audit_rules.id"), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False)
    trigger = db.Column(db.String(16), nullable=False, default="manual")
    attempt = db.Column(db.Integer, nullable=False, default=1)
    scanned_records = db.Column(db.Integer, nullable=False, default=0)
    matched_records = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    rule = db.relationship("AuditRule", back_populates="executions")


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


class RiskScore(db.Model):
    """Explainable point-in-time risk assessment for one audit rule."""

    __tablename__ = "risk_scores"

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("audit_rules.id"), nullable=False, index=True)
    audit_area_id = db.Column(db.Integer, db.ForeignKey("audit_areas.id"), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    level = db.Column(db.String(16), nullable=False)
    alarm_count = db.Column(db.Integer, nullable=False, default=0)
    open_alarm_count = db.Column(db.Integer, nullable=False, default=0)
    components = db.Column(db.JSON, nullable=False, default=dict)
    explanation = db.Column(db.Text, nullable=False)
    calculated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    rule = db.relationship("AuditRule", back_populates="risk_scores")
    audit_area = db.relationship("AuditArea", back_populates="risk_scores")


class User(db.Model):
    """Local application identity. Passwords are stored only as strong hashes."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="viewer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class AuditEvent(db.Model):
    """Append-only record of security and business-significant actions."""

    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.String(80), nullable=True)
    details = db.Column(db.JSON, nullable=False, default=dict)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    actor = db.relationship("User")


class Notification(db.Model):
    """Delivery-neutral notification outbox (in-app today, adapters later)."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(32), nullable=False, default="in_app")
    recipient = db.Column(db.String(255), nullable=False, default="auditors")
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    metadata_json = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
