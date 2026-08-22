"""Authentication, authorization, audit logging and security routes."""

from functools import wraps

from flask import Blueprint, current_app, g, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from models import AuditEvent, User, db


ROLES = {"viewer", "auditor", "admin"}
ROLE_LEVEL = {"viewer": 0, "auditor": 1, "admin": 2}
security_bp = Blueprint("security", __name__)


@security_bp.get("/login")
def login_page():
    return render_template("login.html")


def hash_password(password):
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    return generate_password_hash(password, method="scrypt")


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def require_role(minimum_role="viewer"):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_app.config.get("AUTH_REQUIRED", True):
                return view(*args, **kwargs)
            user = current_user()
            if not user or not user.is_active:
                return jsonify(error="authentication required"), 401
            if ROLE_LEVEL.get(user.role, -1) < ROLE_LEVEL[minimum_role]:
                return jsonify(error="insufficient permissions"), 403
            g.user = user
            return view(*args, **kwargs)
        return wrapped
    return decorate


def record_event(action, entity_type, entity_id=None, details=None, actor=None):
    user = actor or getattr(g, "user", None) or current_user()
    event = AuditEvent(
        actor_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details or {},
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(event)
    return event


@security_bp.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not check_password_hash(user.password_hash, password):
        record_event("login_failed", "user", details={"email": email})
        db.session.commit()
        return jsonify(error="invalid credentials"), 401
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    g.user = user
    record_event("login", "user", user.id)
    db.session.commit()
    return jsonify(id=user.id, email=user.email, role=user.role)


@security_bp.post("/api/auth/logout")
@require_role()
def logout():
    record_event("logout", "user", g.user.id)
    db.session.commit()
    session.clear()
    return "", 204


@security_bp.get("/api/auth/me")
@require_role()
def me():
    return jsonify(id=g.user.id, email=g.user.email, role=g.user.role)


@security_bp.post("/api/users")
@require_role("admin")
def create_user():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    role = str(payload.get("role", "viewer"))
    if "@" not in email or role not in ROLES:
        return jsonify(error="valid email and role are required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="user already exists"), 409
    try:
        password_hash = hash_password(str(payload.get("password", "")))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    user = User(email=email, password_hash=password_hash, role=role)
    db.session.add(user)
    db.session.flush()
    record_event("user_created", "user", user.id, {"email": email, "role": role})
    db.session.commit()
    return jsonify(id=user.id, email=user.email, role=user.role), 201


@security_bp.get("/api/audit-events")
@require_role("admin")
def audit_events():
    events = AuditEvent.query.order_by(AuditEvent.created_at.desc()).limit(500).all()
    return jsonify([{
        "id": event.id, "actor_id": event.actor_id, "action": event.action,
        "entity_type": event.entity_type, "entity_id": event.entity_id,
        "details": event.details, "created_at": event.created_at.isoformat(),
    } for event in events])
