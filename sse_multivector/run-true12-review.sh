#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/.." && pwd)"
binary="$root/target/release/sse-mask-review"

if [[ ! -x "$binary" ]]; then
    printf 'Missing reviewer: %s\nBuild first:\n' "$binary" >&2
    printf 'cd %q\nnix develop -c cargo build --release --jobs 2 --bin sse-mask-review\n' "$root" >&2
    exit 1
fi

exec "$binary" review-membership \
    "$here/navigation-research-v1/TRUE12/membership-review.json" \
    "$root/target/true12-membership-review-session.json" "$@"
