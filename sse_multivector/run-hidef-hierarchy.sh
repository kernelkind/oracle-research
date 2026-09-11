#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
seed=123
case "${1:-}" in
    123|124|125) seed="$1"; shift ;;
    ''|--*) ;;
    *) echo "Usage: $0 [123|124|125] [--start-at GROUP] [--check]" >&2
       exit 2 ;;
esac
series=HDFv1
forward=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --graph-policy)
            [[ "$series" == HDFv1 && $# -ge 2 ]] || { echo 'Expected one graph policy.' >&2; exit 2; }
            case "$2" in
                original|mutual_best_per_note|strongest_edges_matched) ;;
                *) echo 'Unknown graph policy.' >&2; exit 2 ;;
            esac
            series="HDFv2/$2"
            shift 2 ;;
        *) forward+=("$1"); shift ;;
    esac
done
binary="$root/target/infomap-review-build/debug/hdbscan-hierarchy"
if [[ ! -x "$binary" ]]; then
    echo "Build first: cd '$root' && CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin hdbscan-hierarchy" >&2
    exit 1
fi
data="$root/sse_multivector/real-note-fine-segmentation-v1"
exec "$binary" \
    "$root/sse_multivector/hidef-experiment-v1/$series/seed$seed/hierarchy.json" \
    "$data/vectors/vector-map.json" "$data/reviewed-input.json" \
    --containment "${forward[@]}"
