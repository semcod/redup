#!/usr/bin/env bash
# scripts/jscpd-run.sh
# Compatibility wrapper for the packaged reDUP jscpd passthrough.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

exec env PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m redup quality jscpd-run "$@"
