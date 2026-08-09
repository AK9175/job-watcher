"""Persist last-known open/closed state per watched URL."""
from __future__ import annotations

import json
from pathlib import Path


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path: Path, state: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def reset_state(path: Path) -> None:
    if path.exists():
        path.unlink()
