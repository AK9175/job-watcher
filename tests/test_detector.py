from jobwatch.detector import apply_snippet, is_open, title_looks_valid

OPEN_HTML = (
    "<html><head><title>Software Engineer — Google Careers</title></head>"
    '<body><a href="./apply?jobId=abc123">Apply</a></body></html>'
)

CLOSED_HTML = (
    "<html><head><title>Software Engineer — Google Careers</title></head>"
    "<body><p>This position is no longer accepting applications.</p></body></html>"
)

NO_TITLE_HTML = "<html><head></head><body><p>Something went wrong</p></body></html>"


def test_open_html_detected():
    assert is_open(OPEN_HTML) is True


def test_closed_html_not_detected():
    assert is_open(CLOSED_HTML) is False


def test_snippet_present_when_open():
    snippet = apply_snippet(OPEN_HTML)
    assert snippet is not None
    assert "apply?jobId=" in snippet


def test_snippet_absent_when_closed():
    assert apply_snippet(CLOSED_HTML) is None


def test_title_recognized_on_careers_page():
    assert title_looks_valid(OPEN_HTML) is True


def test_title_not_recognized_when_missing():
    assert title_looks_valid(NO_TITLE_HTML) is False
