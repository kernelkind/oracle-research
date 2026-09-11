"""Inspect NMR02 support after excluding every mask of each query's note.

This tests recovery of frozen group membership, not independent semantic truth:
the groups themselves were discovered using the complete corpus.
"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
results_path = root / 'NMR02/results.json'
evidence_path = root.parent / 'geometric-hierarchy-v1/GDC09/evidence.json'
results = json.loads(results_path.read_text())
evidence = json.loads(evidence_path.read_text())
output = []
for group in results:
    anchor_set = set(group['anchor_rows'])
    notes = {}
    for row in group['anchor_rows']:
        entry = evidence[row]['aliases'][0]
        note = entry['note_short_id']
        neighbors = group['neighbors'][row]
        assert all(evidence[w]['aliases'][0]['note_short_id'] != note for w in neighbors)
        recovered = len(neighbors) == 2 and all(w in anchor_set for w in neighbors)
        notes.setdefault(note, []).append(dict(
            vector=entry['short_id'], row=row, recovered=recovered,
            neighbors=[dict(row=w, vector=evidence[w]['aliases'][0]['short_id'],
                            note=evidence[w]['aliases'][0]['note_short_id'],
                            fragments=evidence[w]['aliases'][0]['fragments'],
                            belongs_to_group=w in anchor_set) for w in neighbors]))
    result = dict(group_id=group['group_id'], note_count=len(notes),
                  recovered_notes=[n for n, rows in notes.items() if any(r['recovered'] for r in rows)],
                  unavailable_two_note_calibration=len(notes) < 3,
                  note_results=notes)
    output.append(result)
    print(group['group_id'], len(result['recovered_notes']), '/', len(notes),
          'notes recovered', '(fewer than two other anchor notes)' if len(notes) < 3 else '')
with (root / 'NMR02/whole-note-holdouts.json').open('x') as destination:
    json.dump(dict(results=output, sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in [results_path, evidence_path]}),
              destination, indent=2)
    destination.write('\n')
