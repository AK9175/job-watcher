"""Notification backends behind a small common interface."""
from __future__ import annotations

import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def notify(self, title: str, message: str, url: str) -> bool:
        """Send a notification. Returns True on success, False on failure.

        Must never raise — callers treat a False return as "log and move on".
        """


class ConsoleNotifier(Notifier):
    """Fallback used when no real notification channel is configured."""

    def notify(self, title: str, message: str, url: str) -> bool:
        print(f"[NOTIFY] {title}: {message} ({url})")
        return True


class NtfyNotifier(Notifier):
    def __init__(self, topic: str, timeout: float = 10.0):
        self.topic = topic
        self.timeout = timeout

    def notify(self, title: str, message: str, url: str) -> bool:
        endpoint = f"https://ntfy.sh/{self.topic}"
        request = urllib.request.Request(
            endpoint,
            data=message.encode("utf-8"),
            method="POST",
            headers={
                "Title": title,
                "Priority": "urgent",
                "Click": url,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, OSError) as e:
            print(f"[notify] failed to send ntfy notification: {e}")
            return False


def get_notifier() -> Notifier:
    """NTFY_TOPIC env var selects the ntfy.sh backend; otherwise print and continue."""
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(
                "::warning::NTFY_TOPIC is not set — this CI run has no notification "
                "channel configured, so no alerts will be sent for any transition "
                "detected this run."
            )
        return ConsoleNotifier()
    return NtfyNotifier(topic)
