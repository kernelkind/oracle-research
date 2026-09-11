"""Read frozen original neighborhoods for remaining chocolate/weather concerns.

No fitted coordinates, new extraction, target labels, or thresholds enter this
diagnostic. Source-note maxima prevent repeated same-note masks from filling
the nearest-neighbor display. All underlying mask evidence remains preserved.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from geometric_experiment import write_json

records = json.loads((ROOT/'GDC09/evidence.json').read_text())
config = json.loads((ROOT/'GDC09/configuration.json').read_text())
x = np.load(ROOT/'GDC09/coordinate-snapshots.npz')['0']
assert x.shape == (len(records), 768)
assert np.allclose(np.linalg.norm(x, axis=1), 1, atol=1e-12, rtol=0)
ids = {a['short_id']: r['row'] for r in records for a in r['aliases']}
targets = ['V762', 'V763', 'V764', 'V765', 'V766',
           'V298', 'V299', 'V301', 'V304', 'V305', 'V307',
           'V489', 'V490', 'V728', 'V601']
comparisons = {}
for v in targets:
    i = ids[v]
    own = {a['note_short_id'] for a in records[i]['aliases']}
    cosine = x @ x[i]
    per_note = {}
    for j in np.argsort(-cosine, kind='stable'):
        for a in records[j]['aliases']:
            note = a['note_short_id']
            if note not in own and note not in per_note:
                per_note[note] = dict(note=note, row=int(j), vector=a['short_id'],
                                      cosine=float(cosine[j]), evidence=records[j])
    ordered = sorted(per_note.values(), key=lambda r: -r['cosine'])
    for rank, item in enumerate(ordered, 1):
        item['distinct_note_rank'] = rank
    requested = (['N016', 'N080', 'N094', 'N048', 'N017'] if v in targets[:5]
                 else ['N039', 'N058', 'N080', 'N024', 'N048', 'N069'])
    comparisons[v] = dict(evidence=records[i], nearest_distinct_notes=ordered[:10],
                          requested_notes=[per_note[n] for n in requested if n in per_note])
write_json(ROOT/'GDC09/remaining-original-neighborhoods.json', dict(
    source='GDC09 snapshot0, identical frozen original unit vectors',
    source_hashes=config['sources'],
    diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    method='Unit-vector dot product; highest-cosine row per distinct other source note; no threshold or fit.',
    targets=comparisons))
for v, details in comparisons.items():
    print(v, ' '.join(details['evidence']['aliases'][0]['fragments']))
    for item in details['nearest_distinct_notes'][:5]:
        a = next(a for a in item['evidence']['aliases'] if a['note_short_id'] == item['note'])
        print(item['distinct_note_rank'], item['note'], item['vector'],
              round(item['cosine'], 6), a['fragments'])
    print('Requested', [(r['note'], r['distinct_note_rank'], round(r['cosine'], 6))
                        for r in details['requested_notes']])
