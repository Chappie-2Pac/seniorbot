"""Minimal service entry point used by the Full-s6 contract skeleton."""

from __future__ import annotations

import argparse
import json
import signal
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a hardware adapter stage.")
    parser.add_argument("--stage", choices=("voice",), default="voice")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps({"stage": args.stage, "status": "ready"}, sort_keys=True))
    if args.check:
        return 0
    stopped = False

    def stop(_signum, _frame) -> None:
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopped:
        time.sleep(1.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
