"""Plain HTTP GET with a browser User-Agent. stdlib only."""
from __future__ import annotations

import urllib.error
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class FetchError(Exception):
    """Raised for network-level failures (DNS, timeout, connection refused, ...)."""


def fetch(url: str, timeout: float = 15.0) -> tuple[int, str]:
    """GET url, returning (status_code, body). Raises FetchError on network failure.

    A non-2xx HTTP response is NOT a FetchError — it's returned as-is so the
    caller can decide how to treat it (e.g. HTTP 404/500 vs a real network outage).
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FetchError(str(e)) from e
