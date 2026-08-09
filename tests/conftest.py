import urllib.request

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Safety net: fail loudly if any test actually tries to hit the network."""

    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted in test")

    monkeypatch.setattr(urllib.request, "urlopen", _blocked)
