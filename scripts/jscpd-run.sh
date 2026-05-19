#!/usr/bin/env bash
# scripts/jscpd-run.sh
# Thin wrapper for jscpd with local/global/npx fallback.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

if command -v jscpd >/dev/null 2>&1; then
  exec jscpd "$@"
fi

if npx --no-install jscpd --version >/dev/null 2>&1; then
  exec npx --no-install jscpd "$@"
fi

if command -v npx >/dev/null 2>&1; then
  exec npx --yes jscpd "$@"
fi

cat <<'EOF' >&2
[jscpd] CLI not available.
        Install globally with: npm install -g jscpd
        Or run in an environment with npx available.
EOF
exit 127
