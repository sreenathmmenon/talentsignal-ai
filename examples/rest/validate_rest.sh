#!/usr/bin/env bash
# Validate every TalentSignal REST endpoint. Defaults to the live API; override with BASE.
#   bash examples/rest/validate_rest.sh
#   BASE=http://localhost:8900 bash examples/rest/validate_rest.sh
set -u
BASE="${BASE:-https://talentsignal-api-production.up.railway.app}"
DIR="$(cd "$(dirname "$0")" && pwd)"
pass=0; fail=0
ck(){ if [ "$1" = "200" ]; then pass=$((pass+1)); echo "  ✓ $2"; else fail=$((fail+1)); echo "  ✗ $2 (HTTP $1)"; fi; }

echo "Validating REST API at: $BASE"
ck "$(curl -sS -m20 -o /dev/null -w '%{http_code}' "$BASE/health")" "GET /health"
ck "$(curl -sS -m20 -o /dev/null -w '%{http_code}' "$BASE/docs")" "GET /docs (Swagger UI)"
ck "$(curl -sS -m20 -o /dev/null -w '%{http_code}' "$BASE/openapi.json")" "GET /openapi.json"
ck "$(curl -sS -m60 -o /dev/null -w '%{http_code}' -X POST "$BASE/rank" -H 'Content-Type: application/json' -d @"$DIR/02_rank_request.json")" "POST /rank"
ck "$(curl -sS -m30 -o /dev/null -w '%{http_code}' -X POST "$BASE/ingest/jd" -H 'Content-Type: application/json' -d @"$DIR/03_ingest_jd_request.json")" "POST /ingest/jd"
ck "$(curl -sS -m30 -o /dev/null -w '%{http_code}' -X POST "$BASE/audit" -H 'Content-Type: application/json' -d @"$DIR/04_audit_request.json")" "POST /audit"
ck "$(curl -sS -m30 -o /dev/null -w '%{http_code}' -X POST "$BASE/compliance" -H 'Content-Type: application/json' -d @"$DIR/05_compliance_request.json")" "POST /compliance"
ck "$(curl -sS -m60 -o /dev/null -w '%{http_code}' -X POST "$BASE/candidate_report" -H 'Content-Type: application/json' -d @"$DIR/06_candidate_report_request.json")" "POST /candidate_report"
echo "  ---- $pass passed, $fail failed ----"
