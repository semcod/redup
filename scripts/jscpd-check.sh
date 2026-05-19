#!/usr/bin/env bash
# scripts/jscpd-check.sh
# Duplicate-budget gate for redup's own source tree.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

MIN_LINES="${JSCPD_MIN_LINES:-10}"
MAX_GROUPS="${JSCPD_MAX_GROUPS:-30}"
MAX_LINES="${JSCPD_MAX_LINES:-600}"
REPORT_DIR="${JSCPD_REPORT_DIR:-.jscpd}"

if [ "$#" -gt 0 ]; then
  scan_paths=("$@")
else
  scan_paths=(src tests test_fuzzy_similarity.py test_universal_fuzzy.py scripts benchmark.py)
fi

mkdir -p "$REPORT_DIR"

# jscpd exits non-zero when it finds duplicates; parse the report ourselves so
# the budget, not raw presence of clones, decides pass/fail.
scripts/jscpd-run.sh "${scan_paths[@]}" \
  --reporters json,console \
  --output "$REPORT_DIR" \
  --min-lines "$MIN_LINES" \
  --silent || true

REPORT_PATH="$REPORT_DIR/jscpd-report.json"
if [ ! -f "$REPORT_PATH" ]; then
  echo "[jscpd] Error: report not generated at $REPORT_PATH" >&2
  exit 1
fi

python3 - "$REPORT_PATH" "$MAX_GROUPS" "$MAX_LINES" <<'PY'
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
max_groups = int(sys.argv[2])
max_lines = int(sys.argv[3])

payload = json.loads(report_path.read_text(encoding="utf-8"))
stats = payload.get("statistics", {}).get("total", {})
groups = int(stats.get("clones", 0))
duplicated_lines = int(stats.get("duplicatedLines", 0))
percentage = float(stats.get("percentage", 0.0))

print(
    f"[jscpd] total_groups={groups} duplicated_lines={duplicated_lines} "
    f"percentage={percentage:.2f}% "
    f"(budget: groups<={max_groups}, lines<={max_lines})"
)

violations = []
if groups > max_groups:
    violations.append(f"groups {groups} > {max_groups}")
if duplicated_lines > max_lines:
    violations.append(f"duplicated_lines {duplicated_lines} > {max_lines}")

if violations:
    print(f"[jscpd] budget exceeded: {', '.join(violations)}", file=sys.stderr)
    raise SystemExit(1)

print("[jscpd] budget OK")
PY
