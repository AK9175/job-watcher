from jobwatch.core import run
from jobwatch.fetcher import FetchError
from jobwatch.notifier import Notifier

OPEN_HTML = (
    "<html><head><title>Foo — Google Careers</title></head>"
    '<body><a href="./apply?jobId=xyz">Apply</a></body></html>'
)
CLOSED_HTML = "<html><head><title>Foo — Google Careers</title></head><body>closed</body></html>"

JOBS = [{"label": "Job A", "url": "https://example.com/a"}]


class FakeNotifier(Notifier):
    def __init__(self, succeed: bool = True):
        self.calls: list[tuple[str, str, str]] = []
        self.succeed = succeed

    def notify(self, title, message, url):
        self.calls.append((title, message, url))
        return self.succeed


def fetch_map(mapping):
    def _fetch(url):
        value = mapping[url]
        if isinstance(value, Exception):
            raise value
        return value

    return _fetch


def test_closed_to_open_fires_exactly_one_notification():
    state = {"https://example.com/a": {"is_open": False, "checked_at": "x"}}
    notifier = FakeNotifier()
    fetch_fn = fetch_map({"https://example.com/a": (200, OPEN_HTML)})

    run(JOBS, state, notifier, fetch_fn=fetch_fn)

    assert len(notifier.calls) == 1
    assert state["https://example.com/a"]["is_open"] is True


def test_steady_open_fires_no_notification():
    state = {"https://example.com/a": {"is_open": True, "checked_at": "x"}}
    notifier = FakeNotifier()
    fetch_fn = fetch_map({"https://example.com/a": (200, OPEN_HTML)})

    run(JOBS, state, notifier, fetch_fn=fetch_fn)

    assert len(notifier.calls) == 0


def test_one_url_failing_does_not_block_others():
    jobs = [
        {"label": "Broken", "url": "https://example.com/broken"},
        {"label": "Good", "url": "https://example.com/good"},
    ]
    state: dict = {}
    notifier = FakeNotifier()
    fetch_fn = fetch_map(
        {
            "https://example.com/broken": FetchError("connection refused"),
            "https://example.com/good": (200, CLOSED_HTML),
        }
    )

    results, any_ok = run(jobs, state, notifier, fetch_fn=fetch_fn)

    assert any_ok is True
    assert results[0].ok is False
    assert results[1].ok is True
    assert "https://example.com/good" in state
    assert "https://example.com/broken" not in state


def test_every_url_failing_reports_not_ok():
    jobs = [{"label": "Broken", "url": "https://example.com/broken"}]
    state: dict = {}
    notifier = FakeNotifier()
    fetch_fn = fetch_map({"https://example.com/broken": FetchError("timed out")})

    _results, any_ok = run(jobs, state, notifier, fetch_fn=fetch_fn)

    assert any_ok is False


def test_notification_failure_still_persists_state():
    state = {"https://example.com/a": {"is_open": False, "checked_at": "x"}}
    notifier = FakeNotifier(succeed=False)
    fetch_fn = fetch_map({"https://example.com/a": (200, OPEN_HTML)})

    run(JOBS, state, notifier, fetch_fn=fetch_fn)

    assert len(notifier.calls) == 1
    assert state["https://example.com/a"]["is_open"] is True


def test_dry_run_never_notifies():
    state = {"https://example.com/a": {"is_open": False, "checked_at": "x"}}
    notifier = FakeNotifier()
    fetch_fn = fetch_map({"https://example.com/a": (200, OPEN_HTML)})

    run(JOBS, state, notifier, fetch_fn=fetch_fn, dry_run=True)

    assert len(notifier.calls) == 0
