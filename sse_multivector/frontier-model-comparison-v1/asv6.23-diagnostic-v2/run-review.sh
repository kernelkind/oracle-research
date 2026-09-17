#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
binary="$root/target/release/model-output-review"
if [[ ! -x "$binary" ]]; then
  printf 'Build from oracle-mvp: nix develop -c cargo build --release --jobs 2 --bin model-output-review\n' >&2
  exit 1
fi
exec "$binary" "$here/review.json" "$@"
