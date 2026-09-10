#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
    I01|I02|I03|I04) run="$1"; shift ;;
    *) echo "Usage: $0 I01|I02|I03|I04 [--start-at GROUP] [--check]" >&2
       echo 'I01: existing graph; I02: 5 neighbors; I03: 10 neighbors; I04: 20 neighbors.' >&2
       exit 2 ;;
esac
binary="$root/target/infomap-review-build/debug/hdbscan-hierarchy"
if [[ ! -x "$binary" ]]; then
    echo "Build first: cd '$root' && CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin hdbscan-hierarchy" >&2
    exit 1
fi
data="$root/sse_multivector/real-note-fine-segmentation-v1"
exec "$binary" \
    "$root/sse_multivector/infomap-experiment-v1/$run/hierarchy.json" \
    "$data/vectors/vector-map.json" "$data/reviewed-input.json" \
    --infomap "$@"
