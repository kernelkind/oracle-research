#!/usr/bin/env python3
"""Combine separate long/short text audits; never select the final 100 notes."""

import collections
import hashlib
import json
from pathlib import Path

from audit_corpus import order

ROOT = Path(__file__).resolve().parent
SHORT = ROOT / 'short-note-audit-v1'


def main():
    review = json.loads((SHORT / 'food-manual-audit.json').read_text())
    pool = {row['candidate_rank']: row for row in map(json.loads, (SHORT / 'food-candidates.jsonl').read_text().splitlines())}
    eligible_ranks = set(map(int, review['eligible_ranks_and_rationale']))
    ineligible_ranks = set(map(int, review['ineligible_ranks_and_rationale']))
    assert not eligible_ranks & ineligible_ranks
    assert eligible_ranks | ineligible_ranks == set(pool) == set(range(1, 121))
    accepted = []
    for rank, rationale in review['eligible_ranks_and_rationale'].items():
        row = pool[int(rank)]
        accepted.append({**row, 'broad_area_eligibility_rationale': rationale, 'original_content_sha256': hashlib.sha256(row['content'].encode()).hexdigest(), 'audit_source_file': 'short-note-audit-v1/food-manual-audit.json'})
    (SHORT / 'food-manually-eligible.json').write_text(json.dumps({'schema_version': 1, 'not_final_100_selection': True, 'notes': accepted}, ensure_ascii=False, indent=2) + '\n')
    old = json.loads((ROOT / 'food-manually-eligible.json').read_text())['notes']
    combined = sorted([{**row, 'audit_source_file': 'food-manual-audit.json'} for row in old] + accepted, key=order)
    assert len({row['note_id'] for row in combined}) == len(combined)
    for row in combined:
        row['selection_order_sha256'] = order(row)
    familiar = []
    for rank in (115, 125):
        row = next(row for row in old if row['candidate_rank'] == rank)
        familiar.append({'note_id': row['note_id'], 'candidate_rank_in_original_pool': rank, 'text': row['content'], 'status': 'Possible prior reviewed/example text flagged by the parent; not independently verified by a historical-artifact search', 'automatic_rejection': False, 'reason': 'Development collection, not strict unseen validation. No old vector or grouping result was consulted.'})
    (ROOT / 'prior-text-familiarity-notes.json').write_text(json.dumps({'schema_version': 1, 'new_exclusions': [], 'notes': familiar, 'other_explicitly_recognized_notes': 'Original food candidate 99 is already quarantined; no additional definite prior toy/example text was recognized in the 120 short notes.'}, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'food-combined-manually-eligible-v2.json').write_text(json.dumps({'schema_version': 2, 'not_final_100_selection': True, 'no_final_short_note_quota': True, 'author_and_copy_checks_must_be_applied_to_combined_final_selection': True, 'notes': combined}, ensure_ascii=False, indent=2) + '\n')
    summary = {
        'schema_version': 1,
        'original_18_word_floor': 'Convenience retrieval screen only, not a semantic requirement. Corrected with a separate bounded 5–17-word audit; original 280 notes were not rereviewed.',
        'short_keyword_length_hits_available': 347,
        'short_complete_notes_reviewed': len(pool),
        'short_eligible_notes': len(accepted),
        'short_ineligible_notes': len(ineligible_ranks),
        'short_eligible_authors': len({row['pubkey'] for row in accepted}),
        'original_eligible_notes_preserved': len(old),
        'combined_eligible_notes': len(combined),
        'combined_eligible_authors': len({row['pubkey'] for row in combined}),
        'combined_max_notes_per_author_before_final_selection': max(collections.Counter(row['pubkey'] for row in combined).values()),
        'combined_artifact': 'food-combined-manually-eligible-v2.json',
        'remaining_steps': 'Actual complete-note token-limit check, combined-pool copy/author controls, final hash-ordered selection of 100 with no short-note quota.',
        'no_models_vectors_or_new_database_scan': True,
        'corpus_io': 'One additional bounded verified 21,813,509-byte read of the same already materialized tmpfs sample. No new long-note audit and no historical vector/grouping inspection.',
    }
    (SHORT / 'manual-audit-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
