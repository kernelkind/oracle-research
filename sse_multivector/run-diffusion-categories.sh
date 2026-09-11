#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
usage() {
    echo "Usage: $0 [--absorb-single-children] [--check] (GDC09 categories and original notes)" >&2
    exit 2
}
check=0
absorb=0
for option in "$@"; do
    case "$option" in
        --check) ((check += 1)) ;;
        --absorb-single-children) ((absorb += 1)) ;;
        *) usage ;;
    esac
done
if (( check > 1 || absorb > 1 )); then
    usage
fi
binary="$root/target/infomap-review-build/debug/sse-subject-navigation"
if [[ ! -x "$binary" ]]; then
    echo "Build first: cd '$root' && CARGO_TARGET_DIR=target/infomap-review-build CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 nix develop --command cargo build --bin sse-subject-navigation" >&2
    exit 1
fi
exec "$binary" --categories \
    "$root/sse_multivector/geometric-hierarchy-v1/GDC09/categories.json" \
    "$root/sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json" "$@"
