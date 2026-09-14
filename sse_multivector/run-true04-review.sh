#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/.." && pwd)"
binary="$root/target/release/true-review"
if [[ ! -x "$binary" ]]; then
  printf 'Missing viewer binary: %s\nBuild the true-review target in the repository Rust development environment first.\n' "$binary" >&2
  exit 1
fi
exec "$binary" "$here/navigation-research-v1/TRUE04/review-pairs.json" "$@"
