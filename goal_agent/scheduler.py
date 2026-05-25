from __future__ import annotations

import argparse
import time

from .loop import run_cycle


def run_forever(poll_seconds: int = 3600) -> None:
    # Cron-compatible lightweight scheduler. It avoids adding an undeclared
    # dependency and leaves systemd/cron integration to deployment docs.
    while True:
        run_cycle("daily")
        time.sleep(poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=3600)
    args = parser.parse_args()
    if args.once:
        run_cycle("daily")
        return 0
    run_forever(args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
