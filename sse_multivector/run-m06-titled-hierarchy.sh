#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
binary="$root/target/merge-rule-review-build/debug/sse-subject-navigation"
if [[ ! -x "$binary" ]]; then
    echo "Build once from $root:" >&2
    echo "CARGO_BUILD_JOBS=2 CARGO_TARGET_DIR=target/merge-rule-review-build nix develop -c cargo build --bin sse-subject-navigation" >&2
    exit 1
fi
exec "$binary" --merge-notes \
    "$root/sse_multivector/merge-rule-exploration-v1/M06.json" \
    "$root/sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json" \
    "$root/sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json" \
    "$root/sse_multivector/merge-rule-exploration-v1/M06-titles.json" \
    "$@"
