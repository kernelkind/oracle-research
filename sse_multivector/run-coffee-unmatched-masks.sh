#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != --check ]]; }; then
    echo "Usage: $0 [--check]" >&2
    exit 2
fi
exec "$root/target/infomap-review-build/debug/sse-subject-navigation" \
    --categories "$root/sse_multivector/navigation-research-v1/TRUE13/coffee-unmatched-masks/categories.json" \
    "$root/sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json" "$@"
