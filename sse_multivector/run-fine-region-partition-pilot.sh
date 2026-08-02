#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
archive="$repo_root/sse_multivector/baselines/communicated-meaning-tev4-1/baseline.tar.zst"
config="$repo_root/sse_multivector/fine-region-partition-v1.json"
output="${1:-$repo_root/sse_multivector/fine-region-partition-result-v1}"
baseline="$(mktemp -d -t sse-fine-region-pilot.XXXXXXXX)"

cleanup() {
  rm -rf "$baseline"
}
trap cleanup EXIT

expected="fff03a8b1ed76e45413def0049cdd9fc3c948ae014d5ac94d72fa62f41f8cfa6"
actual="$(sha256sum "$archive" | cut -d ' ' -f 1)"
if [[ "$actual" != "$expected" ]]; then
  echo "baseline archive hash mismatch: expected $expected, got $actual" >&2
  exit 1
fi

tar --zstd -xf "$archive" -C "$baseline"
cd "$repo_root"
nix develop -c cargo run --release --bin sse-fine-region-pilot -- \
  run "$config" "$baseline" "$output"
nix develop -c cargo run --release --bin sse-fine-region-pilot -- \
  verify "$config" "$baseline" "$output"
