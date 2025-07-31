from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_active(self):
        return self.active
    last_login = db.Column(db.DateTime)
    
    # Foreign Keys
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    # Relationships
    audit_areas = db.relationship('AuditArea', backref='owner', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def get_role(self):
        """Get the role name for the user"""
        if self.role_id:
            user_role = Role.query.get(self.role_id)
            return user_role.name if user_role else 'user'
        return 'user'
    
    def get_user_role(self):
        """Get the role name for the user"""
        return self.get_role()

class AuditArea(db.Model):
    __tablename__ = 'audit_areas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    data_sources = db.relationship('DataSource', backref='audit_area', lazy='dynamic', cascade='all, delete-orphan')
    rules = db.relationship('AuditRule', backref='audit_area', lazy='dynamic', cascade='all, delete-orphan')
    alarms = db.relationship('Alarm', backref='audit_area', lazy='dynamic', cascade='all, delete-orphan')

class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    source_type = db.Column(db.String(32), nullable=False)  # database, file, api
    connection_string = db.Column(db.Text)
    config = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    sync_status = db.Column(db.String(32), default='pending')  # pending, success, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    audit_area_id = db.Column(db.Integer, db.ForeignKey('audit_areas.id'), nullable=False)
    
    # Relationships
    data_mappings = db.relationship('DataMapping', backref='data_source', lazy='dynamic', cascade='all, delete-orphan')
    rule_data_sources = db.relationship('RuleDataSource', lazy='dynamic', cascade='all, delete-orphan', overlaps="data_sources,related_rules")

class DataMapping(db.Model):
    __tablename__ = 'data_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    source_field = db.Column(db.String(128), nullable=False)
    target_field = db.Column(db.String(128), nullable=False)
    field_type = db.Column(db.String(32), nullable=False)  # string, number, date, boolean
    is_required = db.Column(db.Boolean, default=False)
    validation_rules = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)

# New Models for Enhanced Anomaly Detection and Fraud Prevention

class RuleFeedback(db.Model):
    """User feedback on rule effectiveness for continuous learning"""
    __tablename__ = 'rule_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    feedback_type = db.Column(db.String(32), nullable=False)  # true_positive, false_positive, false_negative
    user_rating = db.Column(db.Integer)  # 1-5 scale
    comments = db.Column(db.Text)
    alarm_id = db.Column(db.Integer, db.ForeignKey('alarms.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    rule_id = db.Column(db.Integer, db.ForeignKey('audit_rules.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class AnomalyDetection(db.Model):
    """Anomaly detection results and patterns"""
    __tablename__ = 'anomaly_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    detection_type = db.Column(db.String(32), nullable=False)  # statistical, ml_based, pattern_based
    anomaly_score = db.Column(db.Float, nullable=False)  # 0.0-1.0
    confidence_level = db.Column(db.Float, nullable=False)  # 0.0-1.0
    data_point = db.Column(db.JSON)  # The anomalous data point
    context_data = db.Column(db.JSON)  # Surrounding context
    algorithm_used = db.Column(db.String(64))
    feature_importance = db.Column(db.JSON)  # Which features contributed most to detection
    is_confirmed = db.Column(db.Boolean, default=None)  # User confirmation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    rule_id = db.Column(db.Integer, db.ForeignKey('audit_rules.id'), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)

class FraudPattern(db.Model):
    """Known fraud patterns and signatures"""
    __tablename__ = 'fraud_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    pattern_name = db.Column(db.String(128), nullable=False)
    pattern_type = db.Column(db.String(32), nullable=False)  # transaction, behavioral, temporal
    pattern_signature = db.Column(db.JSON, nullable=False)  # Pattern characteristics
    risk_score = db.Column(db.Float, nullable=False)  # 0.0-1.0
    frequency_threshold = db.Column(db.Integer, default=1)  # How many occurrences trigger alert
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_detected = db.Column(db.DateTime)
    detection_count = db.Column(db.Integer, default=0)
    
    # Foreign Keys
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class SecurityEvent(db.Model):
    """Security events and access monitoring"""
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(32), nullable=False)  # login, access, permission_change
    risk_score = db.Column(db.Float, default=0.0)  # 0.0-1.0
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(512))
    location = db.Column(db.String(128))  # Geolocation
    device_fingerprint = db.Column(db.String(256))
    session_id = db.Column(db.String(128))
    is_suspicious = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class RiskScore(db.Model):
    """Risk scoring for users, IPs, and entities"""
    __tablename__ = 'risk_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(32), nullable=False)  # user, ip, account, transaction
    entity_id = db.Column(db.String(128), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)  # 0.0-1.0
    risk_factors = db.Column(db.JSON)  # Contributing factors
    calculation_method = db.Column(db.String(64))  # ml_model, rule_based, hybrid
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Time-based risk tracking
    daily_score = db.Column(db.Float)
    weekly_score = db.Column(db.Float)
    monthly_score = db.Column(db.Float)

class ModelPerformance(db.Model):
    """ML model performance tracking"""
    __tablename__ = 'model_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(64), nullable=False)
    model_version = db.Column(db.String(32))
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    false_positive_rate = db.Column(db.Float)
    false_negative_rate = db.Column(db.Float)
    training_data_size = db.Column(db.Integer)
    training_duration = db.Column(db.Float)  # in seconds
    last_trained = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    rule_id = db.Column(db.Integer, db.ForeignKey('audit_rules.id'), nullable=False)

class AuditRule(db.Model):
    __tablename__ = 'audit_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    rule_type = db.Column(db.String(32), nullable=False)  # threshold, anomaly, compliance, fraud_detection, time_series, system_monitoring
    condition = db.Column(db.Text, nullable=False)
    threshold_value = db.Column(db.Float)
    severity = db.Column(db.String(16), default='medium')  # low, medium, high, critical
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered = db.Column(db.DateTime)
    trigger_count = db.Column(db.Integer, default=0)
    
    # Advanced Rule Features for AI/ML
    algorithm = db.Column(db.String(64))  # isolation_forest, autoencoder, one_class_svm, random_forest, prophet, arima
    sensitivity = db.Column(db.Float, default=0.5)  # Algorithm sensitivity (0.0-1.0)
    confidence_threshold = db.Column(db.Float, default=0.8)  # Minimum confidence for alerts
    risk_category = db.Column(db.String(64))  # financial, security, operational, compliance
    execution_frequency = db.Column(db.String(32), default='hourly')  # real_time, hourly, daily, weekly
    performance_score = db.Column(db.Float, default=0.0)  # Rule effectiveness score
    false_positive_rate = db.Column(db.Float, default=0.0)
    model_config = db.Column(db.JSON)  # Algorithm-specific parameters
    training_data_range = db.Column(db.Integer, default=30)  # Days of historical data for training
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    audit_area_id = db.Column(db.Integer, db.ForeignKey('audit_areas.id'), nullable=False)
    primary_data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=True)  # Ana veri kaynağı
    
    # Relationships
    alarms = db.relationship('Alarm', backref='rule', lazy='dynamic')
    rule_feedback = db.relationship('RuleFeedback', backref='rule', lazy='dynamic', cascade='all, delete-orphan')
    primary_data_source = db.relationship('DataSource', foreign_keys=[primary_data_source_id], backref='primary_rules')
    data_sources = db.relationship('DataSource', secondary='rule_data_sources', backref='related_rules', overlaps="rule_data_sources")
    rule_data_sources = db.relationship('RuleDataSource', lazy='dynamic', cascade='all, delete-orphan', overlaps="data_sources,related_rules")

class Alarm(db.Model):
    __tablename__ = 'alarms'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    message = db.Column(db.Text)
    severity = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(16), default='open')  # open, acknowledged, resolved
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    # Data source and record tracking
    source_data_info = db.Column(db.JSON)  # Information about source data and specific records
    affected_records = db.Column(db.JSON)  # Details of affected records with row numbers/IDs
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))  # Primary data source
    
    # Foreign Keys
    audit_area_id = db.Column(db.Integer, db.ForeignKey('audit_areas.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('audit_rules.id'))
    acknowledged_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    data_source = db.relationship('DataSource', backref='alarms')

class RuleDataSource(db.Model):
    """Junction table for rule-data source many-to-many relationship"""
    __tablename__ = 'rule_data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('audit_rules.id'), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)
    priority = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships with overlap warnings resolved  
    rule = db.relationship('AuditRule', overlaps="data_sources,related_rules,rule_data_sources")
    data_source = db.relationship('DataSource', overlaps="data_sources,related_rules,rule_data_sources")
    
    __table_args__ = (db.UniqueConstraint('rule_id', 'data_source_id'),)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(64), nullable=False)
    resource_type = db.Column(db.String(32), nullable=False)
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class DataQualityCheck(db.Model):
    __tablename__ = 'data_quality_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    check_type = db.Column(db.String(32), nullable=False)  # completeness, accuracy, consistency
    field_name = db.Column(db.String(128))
    expected_value = db.Column(db.String(256))
    actual_value = db.Column(db.String(256))
    status = db.Column(db.String(16), nullable=False)  # pass, fail, warning
    error_message = db.Column(db.Text)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)
