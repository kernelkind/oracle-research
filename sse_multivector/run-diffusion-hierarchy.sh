#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
group=1487
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
    group="$1"
    shift
fi
options=()
if [[ "${1:-}" == --check ]]; then
    options=(--check)
    shift
fi
if (( $# )); then
    echo "Usage: $0 [GROUP_ID] [--check] (GDC09; default group 1487; root 1753)" >&2
    exit 2
fi
binary="$root/target/infomap-review-build/debug/hdbscan-hierarchy"
if [[ ! -x "$binary" ]]; then
    echo "Build first: cd '$root' && CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin hdbscan-hierarchy" >&2
    exit 1
fi
data="$root/sse_multivector/real-note-fine-segmentation-v1"
exec "$binary" \
    "$root/sse_multivector/geometric-hierarchy-v1/GDC09/viewer.json" \
    "$data/vectors/vector-map.json" "$data/reviewed-input.json" \
    --containment --start-at "$group" "${options[@]}"
