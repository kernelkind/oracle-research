#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 123|124|125 NEW_OUTPUT_DIRECTORY [--graph-policy original|mutual_best_per_note|strongest_edges_matched] [--plan]" >&2
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
output="$2"
shift 2
extra=()
policy_args=()
run_id="HDFv1-seed$seed"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)
            [[ ${#extra[@]} == 0 ]] || { echo 'Duplicate --plan.' >&2; exit 2; }
            extra=(--plan); shift ;;
        --graph-policy)
            [[ ${#policy_args[@]} == 0 && $# -ge 2 ]] || { echo 'Expected one graph policy.' >&2; exit 2; }
            case "$2" in
                original|mutual_best_per_note|strongest_edges_matched) ;;
                *) echo 'Unknown graph policy.' >&2; exit 2 ;;
            esac
            policy_args=(--graph-policy "$2")
            run_id="HDFv2-$2-seed$seed"
            shift 2 ;;
        *) echo 'Only --graph-policy and --plan may follow the output directory.' >&2; exit 2 ;;
    esac
done
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
    --run-id "$run_id" --seed "$seed" --output "$output" "${policy_args[@]}" \
    --minres .001 --maxres 25 --density .1 --neighbors 10 \
    --persistence 5 --consensus-percent 75 "${extra[@]}"
