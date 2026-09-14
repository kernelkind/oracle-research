#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../.." && pwd)"
cd "$root"
binary="$root/target/release/sse-mask-review"
if [[ ! -x "$binary" ]]; then
  printf 'Build first: nix develop -c cargo build --release --jobs 2 --bin sse-mask-review\n' >&2
  exit 1
fi
exec "$binary" review-titles \
  "$here/review-all-failures.json" \
  "$root/target/hdbv2-node-description-v16-v18-all-failures-session.json" \
  --comments "$here/review-all-failures-comments.json" "$@"
