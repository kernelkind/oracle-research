#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$HERE/frontier_runner"
if command -v node >/dev/null 2>&1 && node -e 'process.exit(Number(process.versions.node.split(".")[0]) < 24 ? 1 : 0)'; then
  exec node "$RUNNER/runner.mjs" "$@"
fi
exec nix shell nixpkgs#nodejs_24 --command node "$RUNNER/runner.mjs" "$@"
