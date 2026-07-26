#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
    echo "usage: $0 CONFIG.json" >&2
    exit 2
fi

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository=$(git -C "$script_directory" rev-parse --show-toplevel)
config=$(realpath -e -- "$1")
binary=${ORACLE_MVP_TOPIC_SAMPLE_BINARY:-"$repository/target/release/topic-map-sample"}
binary=$(realpath -e -- "$binary")
image='pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427'

if [[ ! -x "$binary" ]]; then
    echo "topic-map sampler binary is not executable: $binary" >&2
    exit 1
fi

mapfile -d '' -t config_paths < <(
    python3 - "$config" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    config = json.load(source)
for field in (
    "source_corpus_path",
    "ordered_event_ids_path",
    "semantic_manifest_path",
    "output_path",
):
    value = config.get(field)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"`{field}` must be a nonempty path")
    sys.stdout.buffer.write(os.path.abspath(value).encode() + b"\0")
PY
)
source_corpus=${config_paths[0]}
ordered_event_ids=${config_paths[1]}
semantic_manifest=${config_paths[2]}
output=${config_paths[3]}
output_parent=$(dirname -- "$output")
output_name=$(basename -- "$output")

if [[ ! -f "$source_corpus/data.mdb" ]]; then
    echo "source NostrDB data file is missing: $source_corpus/data.mdb" >&2
    exit 1
fi
if [[ ! -f "$ordered_event_ids" || ! -f "$semantic_manifest" ]]; then
    echo "sample source artifacts must already exist" >&2
    exit 1
fi
if [[ ! -d "$output_parent" ]]; then
    echo "sample output parent must already exist: $output_parent" >&2
    exit 1
fi
if [[ -e "$output" ]]; then
    echo "sample output already exists: $output" >&2
    exit 1
fi
if [[ "$(findmnt -n -o FSTYPE -T "$output_parent")" != "tmpfs" ]]; then
    echo "sample output parent must be tmpfs: $output_parent" >&2
    exit 1
fi
output_parent=$(realpath -e -- "$output_parent")
tmpfs_mount=$(realpath -e -- "$(findmnt -n -o TARGET -T "$output_parent")")
if [[ "$output_parent" == "$tmpfs_mount" ]]; then
    echo "sample output parent must be a dedicated directory below the tmpfs mount: $output_parent" >&2
    exit 1
fi

container_config="$output_parent/.topic-sample-config.json"
if [[ -e "$container_config" ]]; then
    echo "temporary container config already exists: $container_config" >&2
    exit 1
fi
python3 - "$config" "$container_config" "$output_name" <<'PY'
import json
import os
import sys

source, destination, output_name = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    config = json.load(handle)
config["source_corpus_path"] = "/input/corpus"
config["ordered_event_ids_path"] = "/input/ordered-event-ids.bin"
config["semantic_manifest_path"] = "/input/semantic-manifest.json"
config["output_path"] = f"/output/{output_name}"
temporary = destination + ".tmp"
with open(temporary, "x", encoding="utf-8") as handle:
    json.dump(config, handle, allow_nan=False, sort_keys=True)
    handle.write("\n")
os.replace(temporary, destination)
PY

container_name="crec113-sample-$$-$RANDOM"
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
    --cgroupns private \
    --log-driver none \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --pids-limit 128 \
    --memory 8g \
    --memory-reservation 4g \
    --memory-swap 8g \
    --cpus 4 \
    --tmpfs /tmp:rw,nosuid,nodev,size=512m \
    --mount "type=bind,src=$source_corpus,dst=/input/corpus,readonly" \
    --mount "type=bind,src=$ordered_event_ids,dst=/input/ordered-event-ids.bin,readonly" \
    --mount "type=bind,src=$semantic_manifest,dst=/input/semantic-manifest.json,readonly" \
    --mount "type=bind,src=$binary,dst=/opt/oracle/topic-map-sample,readonly" \
    --mount "type=bind,src=/nix/store,dst=/nix/store,readonly" \
    --mount "type=bind,src=$output_parent,dst=/output" \
    --entrypoint /opt/oracle/topic-map-sample \
    "$image" /output/.topic-sample-config.json)

timeout --signal=TERM --kill-after=15s 1800 docker start -a "$container"
