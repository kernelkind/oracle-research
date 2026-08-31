#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
    echo "usage: $0 CONFIG.json" >&2
    exit 2
fi

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository=$(git -C "$script_directory" rev-parse --show-toplevel)
config=$(realpath -e -- "$1")
image='pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427'
declared_image=$(python3 - "$config" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    runtime = json.load(source).get("runtime")
if runtime is not None:
    image = runtime.get("container_image")
    if not isinstance(image, str) or not image:
        raise SystemExit("runtime container image must be a nonempty string")
    print(image)
PY
)
if [[ -n "$declared_image" && "$declared_image" != "$image" ]]; then
    echo "frozen runtime container image does not match the guarded image" >&2
    exit 1
fi

mapfile -d '' -t config_paths < <(
    python3 - "$config" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    config = json.load(source)
for value in (
    config["input"]["matrix_path"],
    config["input"]["note_ids_path"],
    config["output_path"],
):
    if not isinstance(value, str) or not value:
        raise SystemExit("guard config paths must be nonempty strings")
    sys.stdout.buffer.write(os.path.abspath(value).encode() + b"\0")
binding = config["input"].get("embedding_manifest")
if binding is None:
    sys.stdout.buffer.write(b"\0")
else:
    if not isinstance(binding, dict):
        raise SystemExit("input embedding manifest binding must be an object")
    value = binding.get("path")
    if not isinstance(value, str) or not value:
        raise SystemExit("embedding manifest path must be a nonempty string")
    sys.stdout.buffer.write(os.path.abspath(value).encode() + b"\0")
PY
)
matrix=${config_paths[0]}
note_ids=${config_paths[1]}
output=${config_paths[2]}
embedding_manifest=${config_paths[3]}
output_parent=$(dirname -- "$output")
output_name=$(basename -- "$output")

if [[ ! -f "$matrix" || ! -f "$note_ids" ]]; then
    echo "guard input files must already exist" >&2
    exit 1
fi
if [[ -n "$embedding_manifest" && ! -f "$embedding_manifest" ]]; then
    echo "guard embedding manifest must already exist" >&2
    exit 1
fi
if [[ ! -d "$output_parent" ]]; then
    echo "guard output parent must already exist" >&2
    exit 1
fi
if [[ -e "$output" ]]; then
    echo "guard output already exists: $output" >&2
    exit 1
fi
if [[ "$(findmnt -n -o FSTYPE -T "$output_parent")" != "tmpfs" ]]; then
    echo "guard output parent must be tmpfs: $output_parent" >&2
    exit 1
fi
output_parent=$(realpath -e -- "$output_parent")
output_parent_identity=$(stat -Lc '%d:%i' -- "$output_parent")
guarded_input_paths=("$matrix" "$note_ids")
if [[ -n "$embedding_manifest" ]]; then
    guarded_input_paths+=("$embedding_manifest")
fi
for guarded_input in "${guarded_input_paths[@]}"; do
    guarded_input=$(realpath -e -- "$guarded_input")
    case "$guarded_input" in
        "$output_parent"|"$output_parent"/*)
            echo "output parent must not contain or alias a guarded input" >&2
            exit 1
            ;;
    esac
    ancestor=$(dirname -- "$guarded_input")
    while :; do
        if [[ "$(stat -Lc '%d:%i' -- "$ancestor")" == "$output_parent_identity" ]]; then
            echo "output parent must not contain or alias a guarded input" >&2
            exit 1
        fi
        if [[ "$ancestor" == "/" ]]; then
            break
        fi
        ancestor=$(dirname -- "$ancestor")
    done
done

container_config="$output_parent/.guard-config.json"
python3 - "$config" "$container_config" "$output_name" <<'PY'
import json
import os
import sys

source, destination, output_name = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    config = json.load(handle)
config["input"]["matrix_path"] = "/input/vectors.f32le"
config["input"]["note_ids_path"] = "/input/note-ids.bin"
if config["input"].get("embedding_manifest") is not None:
    config["input"]["embedding_manifest"]["path"] = "/input/manifest.json"
config["output_path"] = f"/output/{output_name}"
temporary = destination + ".tmp"
with open(temporary, "x", encoding="utf-8") as handle:
    json.dump(config, handle, allow_nan=False, sort_keys=True)
    handle.write("\n")
os.replace(temporary, destination)
PY

devices=()
guarded_paths=(/ "$repository" "$matrix" "$note_ids")
if [[ -n "$embedding_manifest" ]]; then
    guarded_paths+=("$embedding_manifest")
fi
for guarded_path in "${guarded_paths[@]}"; do
    filesystem=$(findmnt -n -o FSTYPE -T "$guarded_path")
    if [[ "$filesystem" == "tmpfs" ]]; then
        continue
    fi
    device=$(findmnt -n -o SOURCE -T "$guarded_path")
    if [[ ! -b "$device" ]]; then
        major_minor=$(findmnt -n -o MAJ:MIN -T "$guarded_path")
        device=$(lsblk -nrpo NAME,MAJ:MIN | awk \
            -v number="$major_minor" '$2 == number {print $1; exit}')
    fi
    if [[ ! -b "$device" ]]; then
        echo "could not resolve a physical block device for $guarded_path" >&2
        exit 1
    fi
    parent_device=$(lsblk -ndo PKNAME "$device" | head -n 1)
    if [[ -n "$parent_device" && -b "/dev/$parent_device" ]]; then
        device="/dev/$parent_device"
    fi
    already_present=false
    for existing in "${devices[@]}"; do
        if [[ "$existing" == "$device" ]]; then
            already_present=true
            break
        fi
    done
    if [[ "$already_present" == false ]]; then
        devices+=("$device")
    fi
done
if [[ "${#devices[@]}" -eq 0 ]]; then
    echo "no physical device was found for container image I/O" >&2
    exit 1
fi

io_arguments=()
for device in "${devices[@]}"; do
    io_arguments+=(
        --device-read-bps "$device:8mb"
        --device-read-iops "$device:256"
        --device-write-bps "$device:2mb"
        --device-write-iops "$device:64"
    )
done
embedding_manifest_mount=()
if [[ -n "$embedding_manifest" ]]; then
    embedding_manifest_mount+=(
        --mount "type=bind,src=$embedding_manifest,dst=/input/manifest.json,readonly"
    )
fi
container_name="crec113-guard-$$-$RANDOM"
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
    --memory 8g \
    --memory-reservation 4g \
    --memory-swap 8g \
    --cpus 4 \
    "${io_arguments[@]}" \
    --tmpfs /tmp:rw,nosuid,nodev,size=512m \
    --mount "type=bind,src=$repository,dst=/workspace,readonly" \
    --mount "type=bind,src=$matrix,dst=/input/vectors.f32le,readonly" \
    --mount "type=bind,src=$note_ids,dst=/input/note-ids.bin,readonly" \
    "${embedding_manifest_mount[@]}" \
    --mount "type=bind,src=$output_parent,dst=/output" \
    --entrypoint sleep \
    "$image" infinity)
docker start "$container" >/dev/null

pid=$(docker inspect --format '{{.State.Pid}}' "$container")
cgroup=$(awk -F: '$1 == "0" {print $3}' "/proc/$pid/cgroup")
for device in "${devices[@]}"; do
    read -r major_hex minor_hex < <(stat -c '%t %T' "$device")
    device_number=$((16#$major_hex)):$((16#$minor_hex))
    io_line=$(awk -v device="$device_number" '$1 == device {print}' \
        "/sys/fs/cgroup${cgroup}/io.max")
    for expected in \
        'rbps=8388608' \
        'wbps=2097152' \
        'riops=256' \
        'wiops=64'
    do
        if [[ "$io_line" != *"$expected"* ]]; then
            echo "verified I/O guard is missing $expected for $device: $io_line" >&2
            exit 1
        fi
    done
done

report=$(timeout --signal=TERM --kill-after=15s 1800 docker exec \
    --env PYTHONDONTWRITEBYTECODE=1 \
    --env PYTHONPATH=/workspace \
    --env HOME=/tmp \
    --env TMPDIR=/tmp \
    --env CUBLAS_WORKSPACE_CONFIG=:4096:8 \
    --env OMP_NUM_THREADS=4 \
    --env MKL_NUM_THREADS=4 \
    "$container" \
    python /workspace/topic_map/worker.py /output/.guard-config.json)
report_temporary="$output_parent/.guard-report.json.tmp"
printf '%s\n' "$report" > "$report_temporary"
mv -- "$report_temporary" "$output_parent/guard-report.json"
