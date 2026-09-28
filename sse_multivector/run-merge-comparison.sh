#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != --check ) ]]; then
    echo "Usage: $0 [--check]" >&2
    exit 2
fi
view="$root/target/hierarchy-build-v1/hr02-merge-comparison-v2/categories.json"
binary="$root/target/infomap-review-build/debug/sse-subject-navigation"
if [[ ! -f "$view" ]]; then
    echo "Saved comparison is missing: $view" >&2
    exit 1
fi
if [[ ! -x "$binary" ]]; then
    echo "Hierarchy browser is missing: $binary" >&2
    exit 1
fi
# Deliberately omit equal-note and single-child collapsing: compare model merges only.
exec "$binary" --categories "$view" \
    "$root/sse_multivector/hierarchy-refresh-v1/masked-posts.json" "$@"
