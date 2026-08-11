#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

vector_config="sse_multivector/crec-119-vector-v2.json"
segment_config="sse_multivector/crec-119-segments-v2.json"
prepared="$repo_root/target/crec-119-500-note-v2/sse-prepared"
worker_output="$repo_root/target/crec-119-500-note-v2/sse-worker-output"
output_parent="$repo_root/target/crec-119-500-note-v2"
checkpoint="$repo_root/target/sse-multivector-diagnostic-v1/checkpoint/subencoder_st5_base.ckpt"
model="$repo_root/target/sse-multivector-diagnostic-v1/model/sentence-t5-base-fc5d4628481afbbaaacd7af6bb07cf9d3865f781"
worker="$repo_root/sse_multivector/worker.py"

nix develop -c python3 sse_multivector/scaled_vector_artifact.py \
  prepare "$vector_config"

if [[ ! -e "$worker_output" ]]; then
  configured_image="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["container_image"])' "$vector_config")"
  image_id="sha256:${configured_image##*@sha256:}"
  actual_image_id="$(docker image inspect "$image_id" --format '{{.Id}}')"
  if [[ "$actual_image_id" != "$image_id" ]]; then
    echo "CREC-119 SSE image identity differs: expected $image_id, got $actual_image_id" >&2
    exit 1
  fi
  mkdir -p "$output_parent"
  docker run \
    --rm \
    --network none \
    --read-only \
    --security-opt no-new-privileges \
    --cap-drop ALL \
    --pids-limit 256 \
    --shm-size 1g \
    --tmpfs /tmp:rw,noexec,nosuid,nodev,size=4g,mode=1777 \
    --user "$(id -u):$(id -g)" \
    --env HOME=/tmp \
    --env XDG_CACHE_HOME=/tmp/cache \
    --env HF_HOME=/tmp/huggingface \
    --mount "type=bind,src=$prepared,dst=/input,readonly" \
    --mount "type=bind,src=$checkpoint,dst=/checkpoint/subencoder_st5_base.ckpt,readonly" \
    --mount "type=bind,src=$model,dst=/model,readonly" \
    --mount "type=bind,src=$worker,dst=/workspace/worker.py,readonly" \
    --mount "type=bind,src=$output_parent,dst=/output" \
    "$image_id" \
    python /workspace/worker.py /input/worker-config.json
fi

nix develop -c python3 sse_multivector/scaled_vector_artifact.py \
  finalize "$vector_config"
nix develop -c cargo run --release --bin scaled-fine-segments -- \
  ensure "$segment_config"
