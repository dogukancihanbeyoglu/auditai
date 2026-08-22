"""Hosted worker profile: run scheduled controls without embedding a scheduler in web workers."""

import argparse
import signal
import time

from app import create_app
from services.scheduler import cycle_as_dict, run_scheduler_cycle


def run_worker(*, once=False, poll_seconds=30, app_factory=create_app) -> int:
    if not 5 <= poll_seconds <= 3600:
        raise ValueError("poll_seconds must be between 5 and 3600")
    application = app_factory()
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        with application.app_context():
            application.logger.info("scheduler_cycle", extra={"cycle": cycle_as_dict(run_scheduler_cycle())})
        if once:
            return 0
        time.sleep(poll_seconds)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=30)
    args = parser.parse_args(argv)
    return run_worker(once=args.once, poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
