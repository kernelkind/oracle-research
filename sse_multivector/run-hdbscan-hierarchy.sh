#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
options=()
default_group=1043
binary="$root/target/debug/hdbscan-hierarchy"
data="$root/sse_multivector/real-note-fine-segmentation-v1"
response="$data/hdbscan-cross-note/response.json"
build_command="cargo build --bin hdbscan-hierarchy"
if [[ "${1:-}" == --selection ]]; then
    options=(--selection "$root/sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1/hierarchy-selection-v1.json")
    default_group=916
    shift
elif [[ "${1:-}" == --note-navigation ]]; then
    options=(--note-navigation)
    default_group=1254
    binary="$root/target/hierarchy-note-view-build/debug/hdbscan-hierarchy"
    response="$data/hdbv3-cross-note-edges-v1/response.json"
    build_command="CARGO_TARGET_DIR=target/hierarchy-note-view-build cargo build --bin hdbscan-hierarchy"
    shift
fi
if (( $# > 1 )) || [[ "${1:-$default_group}" == *[!0-9]* || -z "${1:-$default_group}" ]]; then
    echo "Usage: $0 [--selection | --note-navigation] [GROUP_ID] (default: condensed 1043; selection 916; merge-tree 1254)" >&2
    exit 2
fi
if [[ ! -x "$binary" ]]; then
    echo "Build once in oracle-mvp's development shell: $build_command" >&2
    exit 1
fi
exec "$binary" \
    "$response" \
    "$data/vectors/vector-map.json" \
    "$data/reviewed-input.json" \
    "${options[@]}" --start-at "${1:-$default_group}"
