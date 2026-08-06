#!/usr/bin/env python3
"""End-to-end + hostile-input assertions (plan §5, handout §6.7 verbatim).

Every hostile-input case in the handout's list must be handled sensibly, not
crash: an empty training CSV, a header-only CSV, a /predict request missing a
required field, a /predict request with an unseen category, and a /predict
request sent before any model has been trained. Also exercises the malformed
raw-row parsing path (sample_broken.csv) and a normal end-to-end case.

Uses an isolated ML_ARTIFACTS_DIR (via env var override read by config.py) so
this script never touches the real ml/artifacts/ the team is using.

Usage: python3 ml/scripts/smoke_test.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ML_ROOT / "data" / "samples"

_isolated_dir = tempfile.mkdtemp(prefix="mlcore_smoke_")
os.environ["ML_ARTIFACTS_DIR"] = _isolated_dir
sys.path.insert(0, str(ML_ROOT))  # ml/mlcore/, not ml/src/mlcore/ (mlcore is an installable package)

failures: list[str] = []
passed: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        passed.append(label)
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label} :: {detail}")
        print(f"  FAIL  {label} :: {detail}")


def main() -> int:
    from mlcore.api import health_check, load_model, predict, train_model

    print("=== 1. Empty training CSV (0 bytes) ===")
    empty_path = Path(_isolated_dir) / "empty.csv"
    empty_path.write_text("")
    result = train_model(csv_path=str(empty_path))
    check("empty CSV returns status=failed, no crash", result["status"] == "failed", str(result))
    check("empty CSV rows_received == 0", result["rows_received"] == 0, str(result))

    print("\n=== 2. Header-only CSV (zero data rows) ===")
    header_only = Path(_isolated_dir) / "header_only.csv"
    header_only.write_text("id,title,genres,runtime,release_date,original_language,keywords,popularity\n")
    result = train_model(csv_path=str(header_only))
    check("header-only CSV returns status=failed, no crash", result["status"] == "failed", str(result))
    check("header-only CSV rows_received == 0", result["rows_received"] == 0, str(result))

    print("\n=== 3. Predict before any model has been trained ===")
    r = predict({"title": "X", "genre": "Thriller", "duration_minutes": 90,
                 "upload_time": "2020-01-01", "language": "en", "tags": ["a"]})
    check("predict-before-train doesn't crash and returns a shaped response",
          set(r.keys()) >= {"trending_probability", "predicted_label", "grounded", "reason"}, str(r))
    check("predict-before-train is grounded=false", r["grounded"] is False, str(r))
    h = health_check()
    check("health_check reports not-ok before a model is loaded", h["status"] != "ok", str(h))

    print("\n=== 4. Malformed training rows (sample_broken.csv) ===")
    broken_result = train_model(csv_path=str(SAMPLES / "sample_broken.csv"))
    check("sample_broken.csv trains without crashing", broken_result["status"] == "complete", str(broken_result))
    check("sample_broken.csv: rows_processed + rows_failed == rows_received",
          broken_result["rows_processed"] + broken_result["rows_failed"] == broken_result["rows_received"],
          str(broken_result))
    check("sample_broken.csv: exactly 5 of 11 rows failed to parse (missing id, malformed genres, "
          "missing popularity, empty title, malformed keywords)",
          broken_result["rows_failed"] == 5, str(broken_result))

    print("\n=== 5. Real end-to-end training (sample_small.csv) ===")
    small_result = train_model(csv_path=str(SAMPLES / "sample_small.csv"))
    check("sample_small.csv trains successfully", small_result["status"] == "complete", str(small_result))
    check("sample_small.csv: no rows dropped (all 60 are clean)",
          small_result["rows_failed"] == 0 and small_result["rows_processed"] == 60, str(small_result))

    print("\n=== 6. Load the freshly trained model ===")
    load_result = load_model()
    check("load_model() succeeds after training", load_result["loaded"] is True, str(load_result))
    h = health_check()
    # sample_small.csv is tiny (60 rows) so the honesty gate may legitimately
    # fail — either "ok" or "degraded" is a correctly-functioning outcome here.
    check("health_check reports ok or degraded (never crashes, never fakes ok on a bad model)",
          h["status"] in ("ok", "degraded"), str(h))

    print("\n=== 7. Valid /predict request ===")
    r = predict({"title": "Midnight Run", "genre": "Thriller", "duration_minutes": 98,
                 "upload_time": "2026-08-06T00:00:00Z", "language": "en", "tags": ["suspense", "indie", "noir"]})
    check("valid request returns a 200-shaped response", "trending_probability" in r, str(r))
    check("valid request's trending_probability is in [0, 1]",
          0.0 <= r["trending_probability"] <= 1.0, str(r))

    print("\n=== 8. Missing required field (genre) ===")
    r = predict({"title": "X", "duration_minutes": 60, "upload_time": "2020-01-01",
                 "language": "en", "tags": ["a"]})
    check("missing genre doesn't crash", "errors" in r, str(r))
    check("missing genre is reported in errors[]", any("genre" in e for e in r["errors"]), str(r))
    check("missing genre -> grounded=false", r["grounded"] is False, str(r))

    print("\n=== 9. Unseen category (genre never seen during training) ===")
    r = predict({"title": "X", "genre": "InterpretiveKabukiDance", "duration_minutes": 60,
                 "upload_time": "2020-01-01", "language": "en", "tags": ["a"]})
    check("unseen genre doesn't crash", "grounded" in r, str(r))
    check("unseen genre -> grounded=false", r["grounded"] is False, str(r))
    check("unseen genre is reported in unknown_fields[]",
          any("genre" in f for f in r["unknown_fields"]), str(r))

    print("\n=== 10. Malformed upload_time doesn't crash ===")
    r = predict({"title": "X", "genre": "Thriller", "duration_minutes": 60,
                 "upload_time": "not-a-date", "language": "en", "tags": ["a"]})
    check("malformed upload_time doesn't crash", "errors" in r, str(r))
    check("malformed upload_time reported in errors[]",
          any("upload_time" in e for e in r["errors"]), str(r))

    print("\n=== 11. predict_batch handles a mixed batch without crashing ===")
    from mlcore.api import predict_batch
    batch = predict_batch([
        {"title": "Good", "genre": "Thriller", "duration_minutes": 60, "upload_time": "2020-01-01",
         "language": "en", "tags": ["a"]},
        {},
        {"title": "Unseen", "genre": "ZZZNotAGenre", "duration_minutes": 60, "upload_time": "2020-01-01",
         "language": "en", "tags": ["a"]},
    ])
    check("predict_batch returns one response per item", len(batch) == 3, str(batch))
    check("predict_batch never crashes on a bad item", all("grounded" in b for b in batch), str(batch))

    print("\n=== 12. train_model() with an invalid algo doesn't crash (regression guard) ===")
    r = train_model(csv_path=str(SAMPLES / "sample_small.csv"), algo="xgboost")
    check("invalid algo doesn't raise, returns status=failed", r["status"] == "failed", str(r))
    check("invalid algo is named in detail", "xgboost" in r["detail"], str(r))

    print("\n=== 13. predict() with a non-dict metadata argument doesn't crash (regression guard) ===")
    for bad_input in [[1, 2, 3], "a raw string body", 42, True, None]:
        r = predict(bad_input)
        check(f"predict({bad_input!r}) doesn't raise", "grounded" in r, str(r))
        check(f"predict({bad_input!r}) -> grounded=false", r["grounded"] is False, str(r))

    print("\n=== 14. Training CSV where every row fails to parse ===")
    all_fail_path = Path(_isolated_dir) / "all_fail.csv"
    all_fail_path.write_text(
        "id,title,genres,runtime,release_date,original_language,keywords,popularity\n"
        "1,Movie A,['Action'],90,2020-01-01,en,['a'],\n"  # missing popularity -> unlabelable
        "2,Movie B,['Drama'],95,2020-01-02,en,['b'],\n"    # missing popularity -> unlabelable
    )
    r = train_model(csv_path=str(all_fail_path))
    check("all-rows-fail CSV returns status=failed, no crash", r["status"] == "failed", str(r))
    check("all-rows-fail CSV: rows_received=2, rows_processed=0, rows_failed=2",
          r["rows_received"] == 2 and r["rows_processed"] == 0 and r["rows_failed"] == 2, str(r))

    print(f"\n{'='*60}\n{len(passed)} passed, {len(failures)} failed\n{'='*60}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
    shutil.rmtree(_isolated_dir, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
