#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
run="$root/sse_multivector/hierarchy-refresh-v1"
view="$run/categories.json"
source="$run/masked-posts.json"
check=()
baseline=false
usage() { echo "Usage: $0 [--baseline] [--check]" >&2; exit 2; }
for arg in "$@"; do
    case "$arg" in
        --baseline)
            if "$baseline"; then usage; fi
            baseline=true
            view="$run/baseline-categories.json"
            source="$root/sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json"
            ;;
        --check)
            if (( ${#check[@]} )); then usage; fi
            check=(--check)
            ;;
        *) usage ;;
    esac
done
binary="$root/target/infomap-review-build/debug/sse-subject-navigation"
if [[ ! -f "$view" ]]; then
    echo "Hierarchy not packaged yet: $view" >&2
    exit 1
fi
exec "$binary" --categories "$view" "$source" --collapse-equal-note-steps "${check[@]}"
