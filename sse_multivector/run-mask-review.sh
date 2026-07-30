#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
proposal="$root/sse_multivector/subject-mask-proposal-v2.json"
run_dir="$root/target/sse-multivector-isolation-v2"
session="$run_dir/subject-mask-review-session.json"
approved="$run_dir/approved-subject-masks.json"

mkdir -p "$run_dir"
cd "$root"
nix develop -c cargo build --release --bin sse-mask-review
exec target/release/sse-mask-review "$proposal" "$session" "$approved"
