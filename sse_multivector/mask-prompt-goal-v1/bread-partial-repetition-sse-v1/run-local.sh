#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
cd "$root"

# Local CPU execution, NOT the container named by the historical worker schema.
# Model and worker identities are unchanged; saved-vector parity gates analysis.
export LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
exec uv run --offline --no-project --python python3.13 \
  --index https://download.pytorch.org/whl/cpu \
  --index-strategy unsafe-best-match \
  --with 'torch==2.13.0+cpu' \
  --with 'transformers==4.57.1' \
  --with 'tokenizers==0.22.2' \
  --with 'numpy==2.5.2' \
  python sse_multivector/worker.py "$here/run/worker-config.json"
