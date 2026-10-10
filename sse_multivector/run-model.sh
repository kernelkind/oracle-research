#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNNER_ROOT="${EXPERIMENT_RUNNER_ROOT:-$(dirname -- "$(dirname -- "$HERE")")/experiment-runner}"
exec "$RUNNER_ROOT/experiment_runner/run-model.sh" "$@"
