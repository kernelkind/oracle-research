#!/usr/bin/env bash
set -euo pipefail
task_runner_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$task_runner_dir/local_model.py" "$@"
