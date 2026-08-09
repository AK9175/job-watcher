"""Check-all-jobs orchestration: fetch, detect, notify on transition, persist state."""
from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Callable

from .detector import apply_snippet, is_open, title_looks_valid
from .fetcher import FetchError, fetch
from .notifier import Notifier

FetchFn = Callable[[str], tuple[int, str]]


@dataclasses.dataclass
class JobCheckResult:
    label: str
    url: str
    ok: bool
    is_open: bool | None = None
    status: int | None = None
    body_size: int | None = None
    snippet: str | None = None
    error: str | None = None
    title_missing: bool = False


def check_job(job: dict, fetch_fn: FetchFn = fetch) -> JobCheckResult:
    label, url = job["label"], job["url"]
    try:
        status, body = fetch_fn(url)
    except FetchError as e:
        return JobCheckResult(label=label, url=url, ok=False, error=str(e))

    if status != 200:
        return JobCheckResult(
            label=label, url=url, ok=False, status=status, error=f"HTTP {status}"
        )

    open_now = is_open(body)
    return JobCheckResult(
        label=label,
        url=url,
        ok=True,
        is_open=open_now,
        status=status,
        body_size=len(body),
        snippet=apply_snippet(body) if open_now else None,
        title_missing=not title_looks_valid(body),
    )


def run(
    jobs: list[dict],
    state: dict,
    notifier: Notifier,
    fetch_fn: FetchFn = fetch,
    verbose: bool = False,
    dry_run: bool = False,
) -> tuple[list[JobCheckResult], bool]:
    """Check every job, print a status line each, notify on closed->open, update state.

    `state` is mutated in place. Returns (results, any_ok) where any_ok is
    True if at least one job was fetched successfully.
    """
    results: list[JobCheckResult] = []
    any_ok = False

    for job in jobs:
        result = check_job(job, fetch_fn)
        results.append(result)

        if not result.ok:
            print(f"[ERROR]  {job['label']}: {result.error}")
            continue

        any_ok = True

        if result.title_missing:
            print(
                f"[WARN]   {job['label']}: page returned 200 but the job title "
                "wasn't recognized — markup may have changed, not reporting closed"
            )

        status_label = "OPEN" if result.is_open else "closed"
        print(f"[{status_label:<6}] {job['label']}")

        if verbose:
            print(f"         HTTP {result.status}, {result.body_size} bytes")
            if result.snippet:
                print(f"         matched: ...{result.snippet}...")

        previous = state.get(result.url, {})
        was_open = previous.get("is_open", False)

        if result.is_open and not was_open:
            if dry_run:
                print("         (dry-run: transition to OPEN — would notify)")
            else:
                title = f"Job opened: {job['label']}"
                message = f"{job['label']} is now accepting applications."
                sent = notifier.notify(title, message, result.url)
                if not sent:
                    print("         notification failed to send (state still updated)")

        state[result.url] = {
            "is_open": result.is_open,
            "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

    return results, any_ok
