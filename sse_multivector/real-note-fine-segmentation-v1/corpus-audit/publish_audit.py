#!/usr/bin/env python3
"""Package the human text-only audit without finalizing an experiment sample."""

import collections
import hashlib
import json
from pathlib import Path

from audit_corpus import AREAS, visible_words
import re

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def load_pool(area):
    return {row['candidate_rank']: row for row in map(json.loads, (ROOT / f'{area}-candidates.jsonl').read_text().splitlines())}


def main():
    review = json.loads((ROOT / 'food-manual-audit.json').read_text())
    pools = {area: load_pool(area) for area in ('food', 'bitcoin', 'ai')}
    accepted = []
    for rank, rationale in review['eligible_ranks_and_rationale'].items():
        row = pools['food'][int(rank)]
        accepted.append({**row, 'broad_area_eligibility_rationale': rationale, 'original_content_sha256': hashlib.sha256(row['content'].encode()).hexdigest()})
    assert len({row['note_id'] for row in accepted}) == len(accepted)
    assert max(collections.Counter(row['pubkey'] for row in accepted).values()) <= 2
    (ROOT / 'food-manually-eligible.json').write_text(json.dumps({'schema_version': 1, 'not_final_100_selection': True, 'notes': accepted}, ensure_ascii=False, indent=2) + '\n')
    initial_path = REPO / 'target/crec-119-500-note-v2/input/notes.json'
    initial = json.loads(initial_path.read_text())['notes']
    initial_counts = {}
    for area, pattern in AREAS.items():
        initial_counts[area] = sum(bool(re.search(pattern, ' '.join(visible_words(row['text'])), re.I)) for row in initial)
    audit = {
        'schema_version': 1,
        'food_complete_notes_reviewed': 280,
        'food_eligible_notes': len(accepted),
        'food_eligible_authors': len({row['pubkey'] for row in accepted}),
        'food_max_notes_per_author': max(collections.Counter(row['pubkey'] for row in accepted).values()),
        'food_unreviewed_candidates': len(pools['food']) - 280,
        'bitcoin_complete_notes_inspected': 45,
        'ai_complete_notes_inspected': 35,
        'initial_500_note_keyword_hits_no_length_filter': initial_counts,
        'initial_500_source_path': str(initial_path.relative_to(REPO)),
        'initial_500_missing_pubkeys': True,
        'recommended_area': review['area'],
        'recommendation_rationale': 'Enough directly reviewed everyday-language notes to select 100 without a new corpus query; multiple original authors, clear variation in preparation, experience and preference, and coherent recurrence stated in different words. No segments or expected memberships are specified.',
        'not_final_100_selection': True,
        'technical_input_limit_not_yet_checked': True,
        'nutrition_claims_are_source_content_not_verified_advice': True,
        'other_area_counts_are_keyword_screened_candidates_not_100_manually_confirmed': True,
        'no_models_called': True,
        'no_vectors_or_clustering_outcomes_read': True,
        'accidental_provenance_search_exposure': 'Nine old mask-fidelity example IDs and expected comparisons, plus an already documented mixed coffee note, were exposed by source-path searching; all ten IDs are quarantined from clean selection. No actual prior outcomes or vectors were read.',
    }
    (ROOT / 'manual-audit-summary.json').write_text(json.dumps(audit, indent=2) + '\n')
    representative_ranks = {'food': [17, 45, 98, 115, 125, 133, 147, 216, 261], 'bitcoin': [14, 20, 21, 31], 'ai': [5, 13, 31, 35]}
    examples = []
    md = ['# Complete representative corpus notes', '', 'These are corpus-audit examples, not a final note selection, generated subjects, or proposed segment memberships. Text is preserved completely; source claims are not verified or endorsed.', '']
    for area, ranks in representative_ranks.items():
        md.extend([f'## {area}', ''])
        for rank in ranks:
            row = pools[area][rank]
            examples.append(row)
            md.extend([f'### Candidate {rank}: {row["note_id"]}', '', f'Author: `{row["pubkey"]}`. Source row: {row["source_row"]}.', '', '```text', row['content'], '```', ''])
    (ROOT / 'representative-complete-notes.json').write_text(json.dumps({'notes': examples}, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'representative-complete-notes.md').write_text('\n'.join(md))
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
