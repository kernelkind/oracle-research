#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
cd "$root"
nix develop -c cargo build --release --jobs 2 --bin model-output-review
exec "$root/target/release/model-output-review" "$here/review.json" "$@"
