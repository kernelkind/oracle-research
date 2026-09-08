#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if (( $# > 1 )) || [[ "${1:-1043}" == *[!0-9]* || -z "${1:-1043}" ]]; then
    echo "Usage: $0 [GROUP_ID] (default: 1043)" >&2
    exit 2
fi
binary="$root/target/debug/hdbscan-hierarchy"
if [[ ! -x "$binary" ]]; then
    echo "Build once in oracle-mvp's development shell: cargo build --bin hdbscan-hierarchy" >&2
    exit 1
fi
data="$root/sse_multivector/real-note-fine-segmentation-v1"
exec "$binary" \
    "$data/hdbscan-cross-note/response.json" \
    "$data/vectors/vector-map.json" \
    "$data/reviewed-input.json" \
    --start-at "${1:-1043}"
