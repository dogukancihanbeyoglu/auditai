"""Hardened WSGI entry point used by the production container."""

import os

if not os.environ.get("SESSION_SECRET"):
    raise RuntimeError("SESSION_SECRET is required in production")

from app import app  # noqa: E402
from production_security import configure_production  # noqa: E402


configure_production(
    app,
    max_content_length=int(os.environ.get("MAX_REQUEST_BYTES", str(10 * 1024 * 1024))),
    rate_limit=int(os.environ.get("RATE_LIMIT_REQUESTS", "120")),
    rate_window=int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60")),
)
