#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
run_dir="$root/target/reference-map-example-v3"
prior_run_dir="$root/target/reference-map-example-v2"
plan="$root/reference_map/crec-116-note-metadata-v3.json"
proposal="$root/reference_map/crec-116-note-proposal-v3.json"
draft="$root/reference_map/crec-116-hierarchy-draft-v3.json"
hierarchy_review_session="$root/reference_map/crec-116-hierarchy-note-branch-review-session-v1.json"
approved_notes="$run_dir/approved-notes.json"
approved_hierarchy="$run_dir/approved-hierarchy.json"

mkdir -p "$run_dir"
cd "$root"
nix develop -c cargo build --release --bin reference-map

if [[ ! -f "$approved_notes" ]]; then
    if [[ ! -f "$run_dir/note-review-session.json" \
        && -f "$prior_run_dir/note-review-session.json" ]]; then
        cp "$prior_run_dir/note-review-session.json" "$run_dir/note-review-session.json"
    fi
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
            "The 48 notes are approved. The hierarchy draft must now be prepared from that exact set."
        exit 2
    fi
    exec target/release/reference-map hierarchy \
        "$approved_notes" \
        "$draft" \
        "$hierarchy_review_session" \
        "$approved_hierarchy"
fi

exec target/release/reference-map navigate "$approved_hierarchy"
