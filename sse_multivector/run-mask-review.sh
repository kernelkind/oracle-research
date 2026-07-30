#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
proposal="$root/sse_multivector/mask-proposal-v1.json"
run_dir="$root/target/sse-multivector-isolation-v1"
session="$run_dir/mask-review-session.json"
approved="$run_dir/approved-masks.json"

mkdir -p "$run_dir"
cd "$root"
nix develop -c cargo build --release --bin sse-mask-review
exec target/release/sse-mask-review "$proposal" "$session" "$approved"
