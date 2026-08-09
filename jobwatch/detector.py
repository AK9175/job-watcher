"""Open/closed detection for Google Careers job req pages.

When a req is accepting applications, the server-rendered HTML contains an
anchor like href="./apply?jobId=..." (resolved against a <base> tag to
.../applications/apply?jobId=...). When closed, the anchor is absent from
the HTML entirely. A substring check on the raw response body is sufficient.
"""
from __future__ import annotations

import re

APPLY_MARKER = "apply?jobId="
SNIPPET_RADIUS = 95  # ~200 chars total around the match

_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def is_open(html: str) -> bool:
    return APPLY_MARKER in html


def apply_snippet(html: str, radius: int = SNIPPET_RADIUS) -> str | None:
    """Return ~200 chars of HTML around the apply marker, or None if absent."""
    idx = html.find(APPLY_MARKER)
    if idx == -1:
        return None
    start = max(0, idx - radius)
    end = min(len(html), idx + len(APPLY_MARKER) + radius)
    return html[start:end]


def page_title(html: str) -> str | None:
    match = _TITLE_RE.search(html)
    if not match:
        return None
    return match.group(1).strip()


def title_looks_valid(html: str) -> bool:
    """Sanity check that this is actually a rendered Google Careers job page.

    Distinguishes "req is closed" from "Google changed their markup" (or
    served an error/interstitial page) by requiring a recognizable <title>.
    """
    title = page_title(html)
    if not title:
        return False
    return "careers" in title.lower()
