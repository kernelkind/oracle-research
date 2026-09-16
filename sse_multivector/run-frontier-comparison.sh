#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$HERE/frontier_runner"
if [[ ! -d "$RUNNER/node_modules/@earendil-works/pi-ai" || ! -d "$RUNNER/node_modules/ajv" ]]; then
  echo 'Install the pinned dependencies in sse_multivector/frontier_runner with npm ci --ignore-scripts first.' >&2
  exit 1
fi
if command -v node >/dev/null 2>&1 && node -e 'process.exit(Number(process.versions.node.split(".")[0]) < 24 ? 1 : 0)'; then
  exec node "$RUNNER/runner.mjs" "$@"
fi
exec nix shell nixpkgs#nodejs_24 --command node "$RUNNER/runner.mjs" "$@"
