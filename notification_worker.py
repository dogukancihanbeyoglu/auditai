"""One-shot notification outbox worker for cron or a platform scheduled job."""

import json
import os

from app import app
from notifications import notification_service


def main():
    with app.app_context():
        result = notification_service.deliver_due(
            max_attempts=int(os.environ.get("NOTIFICATION_MAX_ATTEMPTS", "5")),
            base_delay_seconds=int(os.environ.get("NOTIFICATION_RETRY_BASE_SECONDS", "60")),
            limit=int(os.environ.get("NOTIFICATION_BATCH_SIZE", "100")),
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
