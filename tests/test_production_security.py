import json
import logging

from flask import Flask

from production_security import JsonFormatter, SlidingWindowLimiter, configure_production


def test_sliding_window_rate_limiter():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=10)
    assert limiter.allow("client", now=0)
    assert limiter.allow("client", now=1)
    assert not limiter.allow("client", now=2)
    assert limiter.allow("client", now=11)


def test_request_limits_headers_and_json_logging():
    app = Flask(__name__)
    app.config["TESTING"] = True
    configure_production(app, max_content_length=8, rate_limit=1, rate_window=30)

    @app.post("/echo")
    def echo():
        return str(len(__import__("flask").request.get_data()))

    client = app.test_client()
    oversized = client.post("/echo", data=b"123456789")
    assert oversized.status_code == 413
    assert oversized.headers["X-Content-Type-Options"] == "nosniff"
    assert client.post("/echo", data=b"1").status_code == 429

    record = logging.LogRecord("auditai", logging.INFO, __file__, 1, "request_complete", (), None)
    record.status = 200
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "request_complete"
    assert payload["status"] == 200
