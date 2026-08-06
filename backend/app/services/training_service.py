"""Backend-side CSV handling for POST /train.

Row counting and hostile-input validation happen here, entirely on the
backend side, before mlcore is ever called — mlcore's train_model() takes a
csv_path, not raw bytes, so a multipart upload must be written to disk first
via persist_uploaded_csv(). The actual training run (the background task
itself) is orchestrated by ml_adapter/mlcore_client.run_training(), not
here — this module owns file handling only.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

from app.core.config import settings


def count_csv_rows(csv_bytes: bytes) -> int:
    """Returns the number of data rows (excluding header) in a CSV payload."""
    text = io.StringIO(csv_bytes.decode("utf-8"))
    reader = csv.reader(text)
    rows = list(reader)
    if not rows:
        return 0
    return max(0, len(rows) - 1)


def persist_uploaded_csv(job_id: str, csv_bytes: bytes) -> str:
    """Writes an uploaded multipart CSV to disk so mlcore.train_model (which
    takes a csv_path, not bytes) has something to read. Returns the path.
    """
    uploads_dir = Path(settings.data_dir) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    path = uploads_dir / f"{job_id}.csv"
    path.write_bytes(csv_bytes)
    return str(path)
