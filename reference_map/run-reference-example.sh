#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
run_dir="$root/target/reference-map-example-v1"
plan="$root/reference_map/crec-115-note-metadata-v1.json"
proposal="$root/reference_map/crec-115-note-proposal-v1.json"
draft="$root/reference_map/crec-116-hierarchy-draft-v1.json"
approved_notes="$run_dir/approved-notes.json"
approved_hierarchy="$run_dir/approved-hierarchy.json"

mkdir -p "$run_dir"
cd "$root"
nix develop -c cargo build --release --bin reference-map

if [[ ! -f "$approved_notes" ]]; then
    if [[ ! -f "$proposal" ]]; then
        target/release/reference-map prepare-notes "$plan" "$proposal"
    fi
    exec target/release/reference-map notes \
        "$proposal" \
        "$run_dir/note-review-session.json" \
        "$approved_notes"
fi

if [[ ! -f "$approved_hierarchy" ]]; then
    if [[ ! -f "$draft" ]]; then
        printf '%s\n' \
            "The 64 notes are approved. The hierarchy draft must now be prepared from that exact set."
        exit 2
    fi
    exec target/release/reference-map hierarchy \
        "$approved_notes" \
        "$draft" \
        "$run_dir/hierarchy-review-session.json" \
        "$approved_hierarchy"
fi

exec target/release/reference-map navigate "$approved_hierarchy"
