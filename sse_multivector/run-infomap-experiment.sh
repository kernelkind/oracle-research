#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# != 2 ]]; then
    echo "Usage: $0 I01|I02|I03|I04 NEW_OUTPUT_DIRECTORY" >&2
    exit 2
fi
neighbors=()
case "$1" in
    I01) ;;
    I02) neighbors=(--neighbors 5) ;;
    I03) neighbors=(--neighbors 10) ;;
    I04) neighbors=(--neighbors 20) ;;
    *) echo 'Expected I01, I02, I03, or I04.' >&2; exit 2 ;;
esac
if [[ -e "$2" ]]; then
    echo 'Output already exists; choose a new directory to preserve previous results.' >&2
    exit 2
fi
data="$root/sse_multivector/real-note-fine-segmentation-v1"
exec nix develop "$root" --command env \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 INFOMAP_NUM_THREADS=1 \
    uv run --no-project --with numpy==2.3.4 --with infomap==2.15.1 python \
    "$root/sse_multivector/infomap_experiment.py" \
    --baseline "$data/hdbv3-cross-note-edges-v1/response.json" \
    --request "$data/hdbv3-cross-note-edges-v1/request.json" \
    --vector-map "$data/vectors/vector-map.json" \
    --notes "$data/reviewed-input.json" \
    --reference "$root/sse_multivector/merge-rule-exploration-v1/M07.json" \
    --run-id "$1" --output "$2" --seed 123 --trials 10 "${neighbors[@]}"
