#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
options=()
default_group=1043
if [[ "${1:-}" == --selection ]]; then
    options=(--selection "$root/sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1/hierarchy-selection-v1.json")
    default_group=916
    shift
fi
if (( $# > 1 )) || [[ "${1:-$default_group}" == *[!0-9]* || -z "${1:-$default_group}" ]]; then
    echo "Usage: $0 [--selection] [GROUP_ID] (default: raw 1043; selection 916)" >&2
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
    "${options[@]}" --start-at "${1:-$default_group}"
