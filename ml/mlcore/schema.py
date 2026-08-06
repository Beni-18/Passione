"""The contract boundary (plan §1, §12).

Both a training-time canonical row and a live /predict body are coerced into
the SAME shape by this module before any feature code ever touches them. This
is what makes train/serve skew structurally impossible rather than merely
unlikely — features.py never has to know whether a row came from a CSV or a
live HTTP request.

Never import sklearn or the model here.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

# The exact /predict contract fields (handout Part 4 — fixed, not ours to change).
CONTRACT_FIELDS = ["title", "genre", "duration_minutes", "upload_time", "language", "tags"]

_TAG_SPLIT_RE = re.compile(r"[|,]")


def _coerce_tags(raw: Any) -> list[str]:
    """Accept a list[str], a "a|b|c" string, or a "a,b,c" string. Never raises."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(t).strip() for t in raw if str(t).strip()]
    if isinstance(raw, str):
        if not raw.strip():
            return []
        return [t.strip() for t in _TAG_SPLIT_RE.split(raw) if t.strip()]
    return []


def _coerce_upload_time(raw: Any) -> tuple[dt.datetime | None, bool]:
    """Parse an ISO-8601 timestamp or a bare YYYY-MM-DD date. Returns (value, ok)."""
    if raw is None or raw == "":
        return None, False
    if isinstance(raw, dt.datetime):
        return raw, True
    if isinstance(raw, dt.date):
        return dt.datetime(raw.year, raw.month, raw.day), True
    if isinstance(raw, str):
        s = raw.strip()
        # Try full ISO-8601 first (handles trailing "Z").
        try:
            return dt.datetime.fromisoformat(s.replace("Z", "+00:00")), True
        except ValueError:
            pass
        # Fall back to a bare date.
        try:
            return dt.datetime.strptime(s, "%Y-%m-%d"), True
        except ValueError:
            return None, False
    return None, False


def _coerce_duration(raw: Any) -> tuple[float | None, bool]:
    if raw is None or raw == "":
        return None, True  # legitimately missing, not an error
    try:
        val = float(raw)
        if val < 0:
            return None, False
        return val, True
    except (TypeError, ValueError):
        return None, False


def validate_metadata(metadata: dict) -> tuple[dict, list[str], list[str]]:
    """Coerce a raw /predict body into a clean canonical dict.

    Returns (clean_dict, errors, unknown_fields). NEVER raises — a malformed
    body always returns a well-formed clean_dict (with defaults filled in) plus
    a list of human-readable problems. unknown_fields is populated later, by
    predict.py, once the model's known-category lists are available; this
    function only fills the structural/type-validation errors.
    """
    # `metadata or {}` only rescues falsy non-dicts (None, [], ""). A truthy
    # non-dict (a JSON array, a bare string/number) would reach `.get()`
    # below and raise AttributeError, violating predict()'s "never raises"
    # guarantee — so check the type explicitly instead.
    metadata = metadata if isinstance(metadata, dict) else {}
    errors: list[str] = []

    title = metadata.get("title")
    if not title or not str(title).strip():
        errors.append("title is missing or empty")
        title = ""
    else:
        title = str(title).strip()

    genre = metadata.get("genre")
    if not genre or not str(genre).strip():
        errors.append("genre is missing or empty")
        genre = None
    else:
        genre = str(genre).strip()

    duration, duration_ok = _coerce_duration(metadata.get("duration_minutes"))
    if not duration_ok:
        errors.append(f"duration_minutes could not be parsed: {metadata.get('duration_minutes')!r}")
        duration = None

    upload_time, time_ok = _coerce_upload_time(metadata.get("upload_time"))
    if not time_ok:
        errors.append(f"upload_time could not be parsed: {metadata.get('upload_time')!r}")

    language = metadata.get("language")
    if not language or not str(language).strip():
        errors.append("language is missing or empty")
        language = None
    else:
        language = str(language).strip().lower()

    tags = _coerce_tags(metadata.get("tags"))

    clean = {
        "title": title,
        "genre": genre,
        "duration_minutes": duration,
        "upload_time": upload_time,
        "language": language,
        "tags": tags,
    }
    return clean, errors, []
