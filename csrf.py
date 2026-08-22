"""Framework-wide session-bound CSRF and same-origin protection."""

import hmac
import secrets
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, request, session


SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
SESSION_KEY = "_csrf_token"
csrf_bp = Blueprint("csrf", __name__)


def csrf_token():
    token = session.get(SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SESSION_KEY] = token
    return token


def _same_origin():
    origin = request.headers.get("Origin")
    if not origin:
        return request.headers.get("Sec-Fetch-Site", "same-origin") not in {"cross-site", "none"}
    supplied = urlsplit(origin)
    expected = urlsplit(request.host_url)
    return supplied.scheme == expected.scheme and supplied.netloc == expected.netloc


@csrf_bp.get("/api/auth/csrf")
def csrf_endpoint():
    return jsonify(csrf_token=csrf_token())


def init_csrf(app):
    """Install protection after final test/runtime configuration is applied."""
    app.config.setdefault("CSRF_ENABLED", not app.testing)
    app.jinja_env.globals["csrf_token"] = csrf_token
    app.register_blueprint(csrf_bp)

    @app.before_request
    def protect_mutation():
        if not current_app.config["CSRF_ENABLED"] or request.method in SAFE_METHODS:
            return None
        if not _same_origin():
            return jsonify(error="cross-origin request rejected"), 403
        supplied = request.headers.get("X-CSRF-Token", "")
        expected = session.get(SESSION_KEY, "")
        if not expected or not supplied or not hmac.compare_digest(expected, supplied):
            return jsonify(error="invalid or missing CSRF token"), 403
        return None
