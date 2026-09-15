"""Compare completed TRUE12 native decisions with the independently frozen review."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path

import true_mask_membership as runner
from hierarcaps_mask_probe import sha256


OUTPUTS = ('analysis.json', 'memberships.json', 'comparison-details.json', 'analysis-manifest.json')
LABELS = ('positive', 'negative', 'uncertain')


def _unique(rows, key):
    result = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value or value in result:
            raise ValueError('unique nonempty ' + key + ' required')
        result[value] = row
    return result


def _review_labels(review, baseline):
    if review.get('experiment') != 'TRUE12' or review.get('phase') != 'before TRUE12 inference':
        raise ValueError('independent before-inference TRUE12 review required')
    categories = _unique(review['categories'], 'title')
    if set(categories) != {node['title'] for node in baseline['nodes']}:
        raise ValueError('review titles differ from frozen categories')
    universe = {f'V{index:03d}' for index in range(1, runner.MASK_COUNT + 1)}
    labels = {}
    for node in baseline['nodes']:
        category = categories[node['title']]
        assigned = {}

        def assign(ids, label, reason=None):
            if not isinstance(ids, list):
                raise ValueError('explicit review mask ID list required')
            for mask_id in ids:
                if mask_id not in universe or mask_id in assigned:
                    raise ValueError('unknown, duplicate or overlapping review mask ID')
                assigned[mask_id] = dict(expected=label, review_reason=reason)

        assign(category['positive_ids'], 'positive')
        for uncertain in category['uncertain']:
            reason = uncertain['reason']
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError('uncertain review reason required')
            assign(uncertain['ids'], 'uncertain', reason)
        for mask_id in universe - assigned.keys():
            assigned[mask_id] = dict(expected='negative', review_reason=None)
        labels[node['group']] = assigned
    return labels


def _validated_scores(inputs, scored, baseline):
    frozen = _unique(inputs, 'id')
    scores = _unique(scored, 'id')
    categories = _unique(baseline['nodes'], 'group')
    if len(categories) != 2 or {node['title'] for node in categories.values()} != set(runner.TITLES):
        raise ValueError('two frozen TRUE12 categories required')
    if not frozen or set(scores) != set(frozen):
        raise ValueError('complete exact scored input coverage required')
    universe = {f'V{index:03d}' for index in range(1, runner.MASK_COUNT + 1)}
    coverage = {group: set() for group in categories}
    ordered = []
    for row_id, source in frozen.items():
        row = scores[row_id]
        if any(row.get(key) != value for key, value in source.items()):
            raise ValueError('scored input or mask provenance changed: ' + row_id)
        group = source['category_id']
        if group not in categories or source['category_title'] != categories[group]['title']:
            raise ValueError('scored category differs from frozen baseline')
        for mask in source['masks']:
            mask_id = mask['short_id']
            if mask_id not in universe or mask_id in coverage[group]:
                raise ValueError('unknown or duplicate scored mask alias')
            coverage[group].add(mask_id)
        native, score = row['predicted'], row['entailment_score']
        if native is not None and type(native) is not bool:
            raise ValueError('Boolean or unresolved native prediction required')
        if isinstance(score, bool) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('finite entailment probability required')
        generated = row['generated_token_ids']
        if (not isinstance(generated, list) or len(generated) < 2
                or any(type(token) is not int for token in generated)
                or type(row['eos_terminated']) is not bool
                or row['eos_terminated'] != (1 in generated[1:])):
            raise ValueError('native generation EOS provenance differs')
        expected_native = ({'1': True, '0': False}.get(row['generated_text'])
                           if row['eos_terminated'] else None)
        if native is not expected_native:
            raise ValueError('native prediction differs from complete generated label')
        if 'threshold_predicted' in row:
            raise ValueError('TRUE12 native results must not contain an assumed cutoff')
        ordered.append(row)
    if any(ids != universe for ids in coverage.values()):
        raise ValueError('all 945 masks in both categories must be scored')
    return ordered


def _counts(rows):
    result = {}
    for expected in LABELS:
        selected = [row for row in rows if row['expected'] == expected]
        result[expected] = dict(total=len(selected),
            yes=sum(row['predicted'] is True for row in selected),
            no=sum(row['predicted'] is False for row in selected),
            unresolved=sum(row['predicted'] is None for row in selected))
    return result


def compare(inputs, scores, baseline, review, reviewed):
    """Return mechanical comparisons only; uncertain judgments stay explicit."""
    scores = _validated_scores(inputs, scores, baseline)
    labels = _review_labels(review, baseline)
    source_notes = _unique(reviewed['notes'], 'note_id')
    details, by_group = [], {node['group']: {} for node in baseline['nodes']}
    for row in scores:
        for mask in row['masks']:
            note = source_notes[mask['note_id']]
            detail = dict(input_id=row['id'], category_id=row['category_id'],
                category_title=row['category_title'], mask_id=mask['short_id'],
                note_id=mask['note_id'], note_short_id=mask['note_short_id'], note_text=note['text'],
                fragments=deepcopy(mask['fragments']), byte_spans=deepcopy(mask['byte_spans']),
                model_input=row['model_input'], premise=row['premise'],
                mask_provenance=deepcopy(mask), predicted=row['predicted'],
                entailment_score=row['entailment_score'], generated_text=row['generated_text'],
                generated_token_ids=list(row['generated_token_ids']),
                eos_terminated=row['eos_terminated'], **labels[row['category_id']][mask['short_id']])
            details.append(detail)
            by_group[row['category_id']][mask['short_id']] = detail
    memberships = runner.derive_note_memberships(scores, baseline)
    summaries = []
    for node in memberships['nodes']:
        group, masks = node['group'], by_group[node['group']]
        for note in node['notes']:
            evidence = [masks[mask_id] for mask_id in note['mask_ids']]
            note['note_short_id'] = evidence[0]['note_short_id']
            note['note_text'] = source_notes[note['note_id']]['text']
            for label in LABELS:
                note[label + '_mask_ids'] = [row['mask_id'] for row in evidence
                                             if row['expected'] == label]
                note['accepted_' + label + '_mask_ids'] = [row['mask_id'] for row in evidence
                    if row['expected'] == label and row['predicted'] is True]
            note['expected'] = ('positive' if note['positive_mask_ids'] else
                                'uncertain' if note['uncertain_mask_ids'] else 'negative')
            note['evidence'] = ('positive' if note['accepted_positive_mask_ids'] else
                'negative-and-uncertain' if note['accepted_negative_mask_ids']
                    and note['accepted_uncertain_mask_ids'] else
                'only-negative' if note['accepted_negative_mask_ids'] else
                'only-uncertain' if note['accepted_uncertain_mask_ids'] else 'none')
        notes = node['notes']
        mask_rows = list(masks.values())
        expected_additions = [note['note_id'] for note in notes
                              if note['expected'] == 'positive' and not note['baseline_recursive']]
        accepted = set(node['accepted_note_ids'])
        summary = dict(group=group, title=node['title'],
            note_counts=_counts(notes), source_note_count=len(notes),
            baseline_recursive_note_count=len(node['baseline_recursive_note_ids']),
            baseline_own_note_count=len(node['baseline_own_note_ids']),
            accepted_note_count=len(accepted), accepted_note_ids=node['accepted_note_ids'],
            added_note_ids=node['added_note_ids'],
            expected_addition_note_ids=expected_additions,
            expected_additions_recovered=[note for note in expected_additions if note in accepted],
            expected_additions_missed=[note for note in expected_additions if note not in accepted],
            baseline_notes_not_accepted=node['missing_baseline_note_ids'],
            clear_positive_notes_missed=[note['note_id'] for note in notes
                if note['expected'] == 'positive' and note['predicted'] is not True],
            clear_negative_notes_accepted=[note['note_id'] for note in notes
                if note['expected'] == 'negative' and note['predicted'] is True],
            clear_negative_note_additions=[note['note_id'] for note in notes
                if note['expected'] == 'negative' and note['predicted'] is True
                and not note['baseline_recursive']],
            uncertain_note_ids=[note['note_id'] for note in notes if note['expected'] == 'uncertain'],
            uncertain_note_additions=[note['note_id'] for note in notes
                if note['expected'] == 'uncertain' and note['predicted'] is True
                and not note['baseline_recursive']],
            unresolved_note_ids=[note['note_id'] for note in notes if note['predicted'] is None],
            positive_notes_accepted_with_positive_evidence=[note['note_id'] for note in notes
                if note['expected'] == 'positive' and note['accepted_positive_mask_ids']],
            positive_notes_accepted_without_positive_evidence=[note['note_id'] for note in notes
                if note['expected'] == 'positive' and note['predicted'] is True
                and not note['accepted_positive_mask_ids']],
            unique_input_count=sum(row['category_id'] == group for row in inputs),
            mask_alias_count=len(mask_rows), mask_counts=_counts(mask_rows),
            clear_positive_masks_missed=[row['mask_id'] for row in mask_rows
                if row['expected'] == 'positive' and row['predicted'] is not True],
            clear_negative_masks_accepted=[row['mask_id'] for row in mask_rows
                if row['expected'] == 'negative' and row['predicted'] is True],
            uncertain_mask_ids=[row['mask_id'] for row in mask_rows if row['expected'] == 'uncertain'],
            unresolved_mask_ids=[row['mask_id'] for row in mask_rows if row['predicted'] is None])
        summaries.append(summary)
    return (dict(experiment='TRUE12', decision='complete native labels; no cutoff',
                 primary_unit='source note, OR over every original mask', categories=summaries),
            memberships, dict(experiment='TRUE12', masks=details))


def _read_json(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique_keys)


def analyze_run(output, review_sha256):
    """Verify completed frozen artifacts before exclusively writing any comparison."""
    for name in OUTPUTS:
        if (output / name).exists():
            raise FileExistsError('preserve earlier analysis: ' + name)
    started = _read_json(output / 'started.json')
    completion = _read_json(output / 'completion.json')
    if started.get('experiment') != 'TRUE12':
        raise ValueError('frozen TRUE12 run required')
    input_hashes = {}

    def verify(name, expected):
        digest = sha256(output / name)
        if digest != expected:
            raise ValueError(name + ' changed')
        input_hashes[name] = digest

    for field, directory in (('data_sha256', 'data'), ('source_sha256', 'source')):
        for name, digest in started[field].items():
            verify(directory + '/' + name, digest)
            if directory == 'source' and sha256(Path(runner.__file__).parent / name) != digest:
                raise ValueError('analysis dependency differs from frozen source: ' + name)
    for name in ('inputs', 'baseline'):
        verify(name + '.json', started[name + '_sha256'])
    verify('semantic-review-before-inference.json', review_sha256)
    verify('scores.jsonl', completion['scores_sha256'])
    verify('first-token-logits.npy', completion['logits_sha256'])
    for name in ('started.json', 'completion.json', 'config.json', 'model-files.json'):
        input_hashes[name] = sha256(output / name)
    review = _read_json(output / 'semantic-review-before-inference.json')
    if review['source_vector_map_sha256'] != started['data_sha256']['vector-map.json']:
        raise ValueError('review source vector map changed')
    config = _read_json(output / 'config.json')
    for field in ('experiment', 'model_id', 'revision', 'dtype', 'device', 'threads',
                  'batch_size', 'max_input_tokens', 'truncation'):
        if config.get(field) != started[field]:
            raise ValueError('inference configuration changed: ' + field)
    if 'threshold' in config or 'threshold_decision' in config:
        raise ValueError('TRUE12 config must not contain an assumed cutoff')
    data = {name: _read_json(output / 'data' / name) for name in runner.DATA_PATHS}
    rebuilt_inputs, rebuilt_baseline = runner.prepare_inputs(*(data[name] for name in runner.DATA_PATHS))
    inputs, baseline = _read_json(output / 'inputs.json'), _read_json(output / 'baseline.json')
    if inputs != rebuilt_inputs or baseline != rebuilt_baseline:
        raise ValueError('frozen input or baseline provenance differs from source data')
    scores = [json.loads(line) for line in (output / 'scores.jsonl').read_text().splitlines()]
    if (len(scores) != completion['pairs'] or len(scores) != started['unique_inputs']
            or started['original_masks'] != runner.MASK_COUNT
            or started['mask_category_pairs'] != 2 * runner.MASK_COUNT):
        raise ValueError('completed inference coverage differs from frozen inputs')
    summary, memberships, details = compare(inputs, scores, baseline, review, data['reviewed-input.json'])
    summary['semantic_review_sha256'] = review_sha256
    for name, value in zip(OUTPUTS, (summary, memberships, details)):
        with (output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write('\n')
    manifest = dict(experiment='TRUE12', semantic_review_sha256=review_sha256,
        input_sha256=input_hashes, output_sha256={name: sha256(output / name) for name in OUTPUTS[:-1]},
        analysis_source_sha256={Path(__file__).name: sha256(Path(__file__))})
    with (output / 'analysis-manifest.json').open('x') as stream:
        json.dump(manifest, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='completed TRUE12 directory')
    parser.add_argument('--review-sha256', required=True, help='independently frozen pre-inference review hash')
    args = parser.parse_args()
    analyze_run(args.output, args.review_sha256)
    print('Verified complete TRUE12 inputs and review; saved native mask and note comparisons.')


if __name__ == '__main__':
    main()
