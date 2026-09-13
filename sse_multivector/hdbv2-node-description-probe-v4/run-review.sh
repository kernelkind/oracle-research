#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../.." && pwd)"
cd "$root"
nix develop -c cargo build --release --jobs 2 --bin sse-mask-review
exec "$root/target/release/sse-mask-review" review-titles \
  "$here/review-uncertain.json" \
  "$root/target/hdbv2-node-description-v4-uncertain-review-session.json" "$@"
