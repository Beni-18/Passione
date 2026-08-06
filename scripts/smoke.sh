#!/usr/bin/env bash
# Curls every endpoint in order against a running `docker compose up` stack,
# exits non-zero on any failure. Does NOT start or stop the stack itself —
# run `make up` (or `docker compose up`) first.
set -euo pipefail

BASE_URL="${PASSIONE_API_BASE:-http://localhost:8000}"
FAIL=0

check() {
  local description="$1"
  local expected_status="$2"
  shift 2
  local actual_status
  actual_status=$(curl -s -o /tmp/smoke_body.json -w '%{http_code}' "$@")
  if [ "$actual_status" != "$expected_status" ]; then
    echo "FAIL: $description — expected $expected_status, got $actual_status"
    cat /tmp/smoke_body.json
    FAIL=1
  else
    echo "OK:   $description ($actual_status)"
  fi
}

check "GET /health"  200 "$BASE_URL/health"
check "GET /"         200 "$BASE_URL/"
check "GET /metrics (no model yet)" 409 "$BASE_URL/metrics"
check "GET /models"   200 "$BASE_URL/models"

check "POST /predict (ungrounded, no model)" 200 \
  -X POST "$BASE_URL/predict" -H 'content-type: application/json' \
  -d @tests/fixtures/predict_ok.json

check "POST /train (multipart CSV)" 202 \
  -X POST "$BASE_URL/train" -F "file=@data/samples/clean_50.csv"

check "POST /train (empty CSV — hostile)" 400 \
  -X POST "$BASE_URL/train" -F "file=@tests/fixtures/empty.csv"

check "POST /train (header-only CSV — hostile)" 400 \
  -X POST "$BASE_URL/train" -F "file=@tests/fixtures/header_only.csv"

check "POST /predict (missing field — hostile)" 422 \
  -X POST "$BASE_URL/predict" -H 'content-type: application/json' \
  -d '{"title":"X","genre":"Comedy"}'

check "GET /status?job_id=does-not-exist" 404 "$BASE_URL/status?job_id=does-not-exist"

exit $FAIL
