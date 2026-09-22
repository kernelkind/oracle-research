#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
cd "$root"
# The review is read-only; the prebuilt tool is enough. Building fetches the
# whole Nix dev shell, so do it only when the binary is missing or forced
# with REVIEW_REBUILD=1.
if [ ! -x "$root/target/release/model-output-review" ] || [ "${REVIEW_REBUILD:-}" = "1" ]; then
  nix develop -c cargo build --release --jobs 2 --bin model-output-review
fi
exec "$root/target/release/model-output-review" "$here/review.json" "$@"
