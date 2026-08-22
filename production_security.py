"""Production-only request protections with no external service dependency."""

import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import jsonify, request


class JsonFormatter(logging.Formatter):
    """Emit one machine-readable JSON object per log record."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("method", "path", "status", "duration_ms", "remote_addr"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class SlidingWindowLimiter:
    """Small per-process limiter suitable for single-instance deployments."""

    def __init__(self, limit=120, window_seconds=60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key, now=None):
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_seconds
        with self._lock:
            entries = self._requests[key]
            while entries and entries[0] <= cutoff:
                entries.popleft()
            if len(entries) >= self.limit:
                return False
            entries.append(now)
            return True


def configure_production(app, *, max_content_length, rate_limit, rate_window):
    app.config.update(MAX_CONTENT_LENGTH=max_content_length)
    limiter = SlidingWindowLimiter(rate_limit, rate_window)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers = [handler]
    app.logger.setLevel(logging.INFO)

    @app.before_request
    def enforce_rate_limit():
        if request.path == "/health":
            return None
        if not limiter.allow(request.remote_addr or "unknown"):
            response = jsonify(error="rate limit exceeded")
            response.status_code = 429
            response.headers["Retry-After"] = str(rate_window)
            return response
        request._auditai_started_at = time.monotonic()
        return None

    @app.after_request
    def log_request(response):
        started = getattr(request, "_auditai_started_at", None)
        duration = round((time.monotonic() - started) * 1000, 2) if started else None
        app.logger.info("request_complete", extra={
            "method": request.method, "path": request.path, "status": response.status_code,
            "duration_ms": duration, "remote_addr": request.remote_addr,
        })
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    return limiter
