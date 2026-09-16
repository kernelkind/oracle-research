#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != --check ]]; }; then
    echo "Usage: $0 [--check]" >&2
    exit 2
fi
binary="$root/target/infomap-review-build/debug/sse-subject-navigation"
if [[ ! -x "$binary" ]]; then
    echo "Build first:" >&2
    echo "cd '$root' && CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin sse-subject-navigation" >&2
    exit 1
fi
exec "$binary" --categories \
    "$root/sse_multivector/navigation-research-v1/TRUE13/categories.json" \
    "$root/sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json" "$@"
