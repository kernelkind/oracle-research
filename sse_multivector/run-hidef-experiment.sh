#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "Usage: $0 123|124|125 NEW_OUTPUT_DIRECTORY [--plan]" >&2
    exit 2
fi
case "$1" in
    123|124|125) seed="$1" ;;
    *) echo 'Expected the frozen primary seed 123 or sensitivity seed 124/125.' >&2; exit 2 ;;
esac
if [[ -e "$2" ]]; then
    echo 'Output already exists; choose a new directory to preserve previous results.' >&2
    exit 2
fi
extra=()
if [[ $# == 3 ]]; then
    [[ "$3" == --plan ]] || { echo 'Only --plan may follow the output directory.' >&2; exit 2; }
    extra=(--plan)
fi
# The Nix-pinned interpreter is needed on NixOS, where a generic uv-managed
# Python cannot start. Python 3.11 also has the mandatory louvain wheel.
exec nix develop "$root" --command \
    nix shell --inputs-from "$root" nixpkgs#python311 --command \
    env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    uv run --no-project --python python3.11 \
    --with-requirements "$root/sse_multivector/hidef-requirements.lock" \
    python "$root/sse_multivector/hidef_experiment.py" \
    --graph-directory "$root/sse_multivector/infomap-experiment-v1/I03" \
    --data-directory "$root/sse_multivector/real-note-fine-segmentation-v1" \
    --run-id "HDFv1-seed$seed" --seed "$seed" --output "$2" \
    --minres .001 --maxres 25 --density .1 --neighbors 10 \
    --persistence 5 --consensus-percent 75 "${extra[@]}"
