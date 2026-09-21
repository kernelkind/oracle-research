"""Read saved receipts and compare masks; no inference or response repair."""
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'position-selection-v4'))
spec = importlib.util.spec_from_file_location('psv4', HERE.parent / 'position-selection-v4/probe.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def main():
    old = previous.records_at(HERE.parent / 'mpv3.13-probe-v1')
    new = previous.records_at(HERE)
    valid = 0
    for case, source, subject in previous.baseline.inputs():
        key = case['id']
        print(f'\n{key} | {subject}')
        for version, record in [('MPv3.13', old[key]), ('MPv3.15', new[key])]:
            raw = record['final_output_raw']
            print(version, 'raw:', raw)
            try:
                ranges = previous.decode(raw, source)
            except ValueError as error:
                print('INVALID:', error)
                continue
            if version == 'MPv3.15':
                valid += 1
            print(previous.baseline.position_check.highlight(source, ranges))
            print('Fragments:', json.dumps([source[s['start']:s['end']] for s in ranges], ensure_ascii=False))
    print(f'Valid responses: {valid}/6. Semantic judgments are separate.')
    print('Usage:', json.dumps({key: sum(r['usage'][key] for r in new.values()) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}, sort_keys=True))


if __name__ == '__main__':
    main()
