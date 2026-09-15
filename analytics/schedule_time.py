"""Banner schedule timestamp parsing.

Accepts several common formats and canonicalizes to "%Y-%m-%d %H:%M:%S":
    2025-01-15 11:00:00
    2025-01-15 11:00
    2025-01-15 11am / 1pm
    2025-01-15          (midnight)
"""
from datetime import datetime
from typing import Optional

FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %I%p",
    "%Y-%m-%d %I:%M%p",
    "%Y-%m-%d",
]


def parse_timestamp(raw: str) -> Optional[datetime]:
    """Parses a user-supplied timestamp; None if unparseable."""
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def canonical(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def now_canonical() -> str:
    return canonical(datetime.utcnow())
