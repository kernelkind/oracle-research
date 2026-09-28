#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != --check ) ]]; then
    echo "Usage: $0 [--check]" >&2
    exit 2
fi
view="$root/target/hierarchy-build-v1/hr02-hdbscan-merge-v1/view/categories.json"
binary="$root/target/infomap-review-build/debug/sse-subject-navigation"
if [[ ! -f "$view" ]]; then
    echo "Saved HR02-NMP07 hierarchy is missing: $view" >&2
    exit 1
fi
if [[ ! -x "$binary" ]]; then
    echo "Hierarchy browser is missing: $binary" >&2
    exit 1
fi
# Only model-approved merges: no additional equal-note or single-child collapse.
exec "$binary" --categories "$view" \
    "$root/sse_multivector/hierarchy-refresh-v1/masked-posts.json" "$@"
