from __future__ import annotations

import json
import os


def parse_time_input(text: str) -> int:
    """Parse a user-supplied time string into seconds.

    Accepts 'MM:SS' or a plain integer string (seconds).
    Raises ValueError on bad input.
    """
    text = text.strip()
    if ":" in text:
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {text!r}")
        return int(parts[0]) * 60 + int(parts[1])
    return int(text)


def settings_path() -> str:
    """Return the path to the settings JSON file."""
    folder = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")),
        "SportsClockApp",
    )
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def load_logo_settings(path: str) -> list[str | None]:
    """Load saved logo paths from *path*. Returns [home, away] or [None, None]."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("logos", [None, None])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return [None, None]


def save_logo_settings(path: str, logo_paths: list[str | None]) -> None:
    """Write logo paths to *path* as JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"logos": logo_paths}, f, indent=2)
