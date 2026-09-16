#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
view="$root/sse_multivector/navigation-research-v1/TRUE14/categories.json"
check=()
baseline=false
for arg in "$@"; do
    case "$arg" in
        --baseline)
            if "$baseline"; then
                echo "Usage: $0 [--baseline] [--check]" >&2
                exit 2
            fi
            baseline=true
            view="$root/sse_multivector/navigation-research-v1/TRUE13/categories-with-mask-ids.json"
            ;;
        --check)
            if (( ${#check[@]} )); then
                echo "Usage: $0 [--baseline] [--check]" >&2
                exit 2
            fi
            check=(--check)
            ;;
        *)
            echo "Usage: $0 [--baseline] [--check]" >&2
            exit 2
            ;;
    esac
done
binary="$root/target/infomap-review-build/debug/sse-subject-navigation"
if [[ ! -x "$binary" ]]; then
    echo "Build first:" >&2
    echo "cd '$root' && CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin sse-subject-navigation" >&2
    exit 1
fi
exec "$binary" --categories "$view" \
    "$root/sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json" "${check[@]}"
