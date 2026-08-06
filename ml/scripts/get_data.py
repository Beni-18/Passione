#!/usr/bin/env python3
"""Downloads movies_train.csv from the movie-popularity-prediction Kaggle
competition into ml/data/raw (plan §3). Idempotent — skips if already present.

Usage: python3 ml/scripts/get_data.py
"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mlcore import config  # noqa: E402


def main() -> int:
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = config.RAW_DATA_DIR / "movies_train.csv"
    if target.exists():
        print(f"Already present: {target} ({target.stat().st_size:,} bytes) — skipping download.")
        return 0

    print("Downloading movies_train.csv from Kaggle (movie-popularity-prediction)...")
    result = subprocess.run(
        ["kaggle", "competitions", "download", "-f", "movies_train.csv",
         "-c", "movie-popularity-prediction", "-p", str(config.RAW_DATA_DIR)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Kaggle download failed:", result.stderr, file=sys.stderr)
        print("Fallback: use ml/data/samples/sample_large.csv to keep the pipeline demonstrable.",
              file=sys.stderr)
        return 1

    zip_path = config.RAW_DATA_DIR / "movies_train.csv.zip"
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(config.RAW_DATA_DIR)
        zip_path.unlink()

    if not target.exists():
        print(f"Download completed but {target} not found — check the zip contents.", file=sys.stderr)
        return 1

    print(f"Done: {target} ({target.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
