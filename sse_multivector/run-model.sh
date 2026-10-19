#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNNER_ROOT="${EXPERIMENT_RUNNER_ROOT:-}"
if [[ -z "$RUNNER_ROOT" ]]; then
  RUNNER_ROOT="$(dirname -- "$HERE")/experiment-runner"
  if [[ ! -d "$RUNNER_ROOT" ]]; then
    RUNNER_ROOT="$(dirname -- "$(dirname -- "$HERE")")/experiment-runner"
  fi
fi
if [[ ! -f "$RUNNER_ROOT/experiment_runner/__init__.py" ]]; then
  echo 'Initialize the experiment-runner submodule or set EXPERIMENT_RUNNER_ROOT to a checkout.' >&2
  exit 1
fi
exec "$RUNNER_ROOT/experiment_runner/run-model.sh" "$@"
