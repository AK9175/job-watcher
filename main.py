#!/usr/bin/env python3
"""Local job-posting watcher for Google Careers reqs.

Usage:
    python3 main.py [--dry-run] [--reset] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jobwatch.core import run
from jobwatch.fetcher import fetch
from jobwatch.notifier import get_notifier
from jobwatch.state import load_state, reset_state, save_state

BASE_DIR = Path(__file__).resolve().parent
JOBS_PATH = BASE_DIR / "jobs.json"
STATE_PATH = BASE_DIR / "state.json"


def load_jobs(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Watch Google Careers job postings for open applications."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check and print, but don't write state.json or send notifications.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear state.json before running (re-triggers the open transition).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log HTTP status, response size, and the matched snippet.",
    )
    parser.add_argument(
        "--test-notify",
        action="store_true",
        help=(
            "Send test OPEN and CLOSED notifications through the configured "
            "backend and exit. Doesn't touch jobs.json or state.json."
        ),
    )
    args = parser.parse_args(argv)

    if args.test_notify:
        notifier = get_notifier()
        opened_ok = notifier.notify(
            "Job opened: TEST",
            "This is a test notification for the OPEN case.",
            "https://example.com/test-open",
        )
        print(f"[test-notify] open notification {'sent' if opened_ok else 'FAILED'}")
        closed_ok = notifier.notify(
            "Job closed: TEST",
            "This is a test notification for the CLOSED case.",
            "https://example.com/test-closed",
        )
        print(f"[test-notify] closed notification {'sent' if closed_ok else 'FAILED'}")
        return 0 if (opened_ok and closed_ok) else 1

    if args.reset:
        reset_state(STATE_PATH)
        print(f"[reset]  cleared {STATE_PATH.name}")

    jobs = load_jobs(JOBS_PATH)
    state = load_state(STATE_PATH)
    notifier = get_notifier()

    _results, any_ok = run(
        jobs,
        state,
        notifier,
        fetch_fn=fetch,
        verbose=args.verbose,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        save_state(STATE_PATH, state)

    if not any_ok:
        print("[FATAL]  every job failed to fetch", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
