#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
    echo "usage: $0 CONFIG.json DEPENDENCIES_DIR" >&2
    exit 2
fi

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository=$(git -C "$script_directory" rev-parse --show-toplevel)
config=$(realpath -e -- "$1")
dependencies=$(realpath -e -- "$2")
pinned_image='pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427'

mapfile -d '' -t config_paths < <(
    python3 - "$config" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    config = json.load(source)
for field in (
    "sample_manifest_path",
    "model_path",
    "dependencies_path",
    "output_path",
):
    value = config.get(field)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"`{field}` must be a nonempty path")
    sys.stdout.buffer.write(os.path.abspath(value).encode() + b"\0")
runtime = config.get("runtime")
if not isinstance(runtime, dict):
    raise SystemExit("`runtime` must be an object")
image = runtime.get("container_image")
if not isinstance(image, str) or not image:
    raise SystemExit("`runtime.container_image` must be a nonempty string")
sys.stdout.buffer.write(image.encode() + b"\0")
PY
)
sample_manifest=${config_paths[0]}
model=${config_paths[1]}
config_dependencies=$(realpath -e -- "${config_paths[2]}")
output=${config_paths[3]}
image=${config_paths[4]}
sample_directory=$(dirname -- "$sample_manifest")
sample_name=$(basename -- "$sample_manifest")
output_parent=$(dirname -- "$output")
output_name=$(basename -- "$output")

if [[ "$config_dependencies" != "$dependencies" ]]; then
    echo "dependency path argument differs from the explicit config path" >&2
    exit 1
fi
if [[ "$image" != "$pinned_image" ]]; then
    echo "encoder config does not name the pinned container image" >&2
    exit 1
fi
if [[ ! -f "$sample_manifest" || ! -f "$sample_directory/sample.jsonl" ]]; then
    echo "encoder sample artifacts are incomplete" >&2
    exit 1
fi
if [[ ! -f "$model/config.json" || ! -f "$model/model.safetensors" ]]; then
    echo "encoder model artifacts are incomplete" >&2
    exit 1
fi
if [[ ! -d "$dependencies/transformers" ]]; then
    echo "pinned Transformers runtime is missing" >&2
    exit 1
fi
if [[ ! -d "$output_parent" ]]; then
    echo "encoder output parent must already exist: $output_parent" >&2
    exit 1
fi
if [[ -e "$output" ]]; then
    echo "encoder output already exists: $output" >&2
    exit 1
fi
for guarded_path in "$sample_directory" "$model" "$dependencies" "$output_parent"; do
    if [[ "$(findmnt -n -o FSTYPE -T "$guarded_path")" != "tmpfs" ]]; then
        echo "encoder runtime path must be tmpfs: $guarded_path" >&2
        exit 1
    fi
done
output_parent=$(realpath -e -- "$output_parent")
tmpfs_mount=$(realpath -e -- "$(findmnt -n -o TARGET -T "$output_parent")")
if [[ "$output_parent" == "$tmpfs_mount" ]]; then
    echo "encoder output parent must be below the tmpfs mount" >&2
    exit 1
fi
output_parent_identity=$(stat -Lc '%d:%i' -- "$output_parent")
for guarded_input in "$sample_directory" "$model" "$dependencies"; do
    guarded_input=$(realpath -e -- "$guarded_input")
    case "$guarded_input" in
        "$output_parent"|"$output_parent"/*)
            echo "output parent must not contain or alias an encoder input" >&2
            exit 1
            ;;
    esac
    ancestor=$guarded_input
    while :; do
        if [[ "$(stat -Lc '%d:%i' -- "$ancestor")" == "$output_parent_identity" ]]; then
            echo "output parent must not contain or alias an encoder input" >&2
            exit 1
        fi
        if [[ "$ancestor" == "/" ]]; then
            break
        fi
        ancestor=$(dirname -- "$ancestor")
    done
done

container_config="$output_parent/.encoder-config.json"
if [[ -e "$container_config" ]]; then
    echo "temporary encoder config already exists: $container_config" >&2
    exit 1
fi
python3 - "$config" "$container_config" "$sample_name" "$output_name" <<'PY'
import json
import os
import sys

source, destination, sample_name, output_name = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    config = json.load(handle)
config["sample_manifest_path"] = f"/sample/{sample_name}"
config["model_path"] = "/model"
config["dependencies_path"] = "/dependencies"
config["output_path"] = f"/output/{output_name}"
temporary = destination + ".tmp"
with open(temporary, "x", encoding="utf-8") as handle:
    json.dump(config, handle, allow_nan=False, sort_keys=True)
    handle.write("\n")
os.replace(temporary, destination)
PY

container_name="crec113-encoder-$$-$RANDOM"
container=
cleanup() {
    if [[ -n "$container" ]]; then
        docker rm -f "$container" >/dev/null 2>&1 || true
    fi
    rm -f -- "$container_config"
}
trap cleanup EXIT

container=$(docker create \
    --name "$container_name" \
    --pull=never \
    --read-only \
    --network none \
    --log-driver none \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --pids-limit 512 \
    --memory 12g \
    --memory-reservation 4g \
    --memory-swap 12g \
    --cpus 20 \
    --tmpfs /tmp:rw,nosuid,nodev,size=2g \
    --mount "type=bind,src=$repository,dst=/workspace,readonly" \
    --mount "type=bind,src=$sample_directory,dst=/sample,readonly" \
    --mount "type=bind,src=$model,dst=/model,readonly" \
    --mount "type=bind,src=$dependencies,dst=/dependencies,readonly" \
    --mount "type=bind,src=$output_parent,dst=/output" \
    --env PYTHONDONTWRITEBYTECODE=1 \
    --env PYTHONPATH=/dependencies:/workspace \
    --env HOME=/tmp \
    --env TMPDIR=/tmp \
    --env HF_HOME=/tmp/huggingface \
    --env HF_HUB_OFFLINE=1 \
    --env TRANSFORMERS_OFFLINE=1 \
    --env TOKENIZERS_PARALLELISM=false \
    --env OMP_NUM_THREADS=20 \
    --env MKL_NUM_THREADS=20 \
    --entrypoint python \
    "$image" /workspace/topic_map/encode_sample.py /output/.encoder-config.json)

report=$(timeout --signal=TERM --kill-after=30s 10800 docker start -a "$container")
report_temporary="$output_parent/.encoder-report.json.tmp"
printf '%s\n' "$report" > "$report_temporary"
mv -- "$report_temporary" "$output_parent/encoder-report.json"
