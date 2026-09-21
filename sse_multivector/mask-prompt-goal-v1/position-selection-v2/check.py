"""Reproduce format checks and inline views directly from saved runner receipts."""
import json
import sys
from dataclasses import replace
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def decode(raw, source):
    spans = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(spans, list):
        raise ValueError('response is not a JSON array')
    previous_end = 0
    for span in spans:
        if not isinstance(span, dict) or set(span) != {'start', 'end'}:
            raise ValueError('each range must contain exactly start and end')
        start, end = span['start'], span['end']
        if type(start) is not int or type(end) is not int:
            raise ValueError('boundaries must be integers')
        if not previous_end <= start < end <= len(source):
            raise ValueError('empty, overlapping, unordered, or out-of-bounds range')
        previous_end = end
    return spans


def highlight(source, spans):
    result, cursor = [], 0
    for span in spans:
        start, end = span['start'], span['end']
        result.extend((source[cursor:start], '⟦', source[start:end], '⟧'))
        cursor = end
    result.append(source[cursor:])
    return ''.join(result)


def main():
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here.parents[1]))
    import extraction_pipeline as pipeline
    plan = json.loads((here / 'plan.json').read_text())
    config = pipeline.PromptRunnerConfig.load(here / plan['config_file'])
    manifest = json.loads((config.run_directory / 'manifest.json').read_text())
    records = [json.loads(line) for line in (config.run_directory / 'results.jsonl').read_text().splitlines()]
    cases = json.loads((here / 'cases.json').read_text())
    jobs = {job.prompt_id: job for job in config.prompts}
    by_id = {record['note_id']: record for record in records}
    if len(records) != len(by_id) or set(by_id) != set(jobs):
        raise ValueError('expected one saved receipt per case; no missing or repeated attempts')
    valid = 0
    for case in cases:
        record = by_id[case['id']]
        pipeline.validate_prompt_receipt(replace(config, prompts=(jobs[case['id']],)), manifest, record)
        body = record['model_result']['request']['body']
        assert len(body['input']) == 1 and body['input'][0]['role'] == 'user'
        assert not body.get('instructions') and not body.get('tools')
        fixtures = json.loads((here / case['source_fixture']).read_text())
        source = next(item['source'] for item in fixtures if item['id'] == case['source_id'])
        print(f"\n{case['id']} | {case['subject']}")
        try:
            spans = decode(record['final_output_raw'], source)
        except ValueError as error:
            print(f'FORMAT INVALID: {error}\n{record["final_output_raw"]}')
            continue
        valid += 1
        print(highlight(source, spans))
        print('Fragments:', json.dumps([source[s['start']:s['end']] for s in spans], ensure_ascii=False))
    totals = {key: sum(record['usage'][key] for record in records) for key in ('input', 'output', 'cacheRead', 'cacheWrite', 'totalTokens')}
    print(f'\nValid range responses: {valid}/{len(cases)}. Semantic correctness requires separate review.')
    print('Usage from runner:', json.dumps(totals, sort_keys=True))


if __name__ == '__main__':
    main()
