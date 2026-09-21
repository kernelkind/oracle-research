"""Read-only four-version comparison using existing receipt checks and decoder."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'position-selection-v4'))
spec = importlib.util.spec_from_file_location('psv4', ROOT / 'position-selection-v4/probe.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

versions = ('13', '15', '16', '17')
records = {v: previous.records_at(ROOT / f'mpv3.{v}-probe-v1') for v in versions}
valid = {v: 0 for v in versions}
for case, source, subject in previous.baseline.inputs():
    print(f"\n{case['id']} | {subject}")
    for v in versions:
        raw = records[v][case['id']]['final_output_raw']
        print(f'MPv3.{v}: {raw}')
        try:
            ranges = previous.decode(raw, source)
        except ValueError as error:
            print('INVALID:', error)
            continue
        valid[v] += 1
        print(previous.baseline.position_check.highlight(source, ranges))
        print('Fragments:', json.dumps([source[s['start']:s['end']] for s in ranges], ensure_ascii=False))
print('Decodable counts:', valid)
for v in ('16', '17'):
    print(f'MPv3.{v} usage:', json.dumps({key: sum(r['usage'][key] for r in records[v].values()) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}))
