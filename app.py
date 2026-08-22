"""AuditAI portfolio prototype.

This repository intentionally uses synthetic or anonymized data only.
"""

import os

from flask import Flask, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app() -> Flask:
    """Create and configure the lightweight portfolio application."""
    application = Flask(__name__)
    application.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "local-demo-only")
    application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1, x_host=1)

    @application.get("/")
    def index():
        return render_template("admin_demo.html")

    @application.get("/health")
    def health():
        return jsonify(status="ok", service="auditai")

    return application


app = create_app()


if __name__ == "__main__":
    debug_enabled = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=5000, debug=debug_enabled)
