"""TRUE14 packaging exercises the full production CLI with frozen-style inputs."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


CODE = Path(__file__).resolve().parent
TITLES = ['Coffee', 'Tea as a beverage', 'Coffee Bean Preparation',
          'Having drunk coffee', 'Appreciating Coffee for Its Flavour', '#coffeechain']


def fixture():
    texts = {'note-1': 'café coffee milk tea', 'note-2': 'same coffee', 'note-3': 'none'}
    source = json.dumps(dict(notes=[dict(note_id=key, text=value)
                                  for key, value in texts.items()]), ensure_ascii=False).encode()
    masks = []
    for index in range(1, 946):
        note, spans = 'note-1', [[6, 12]]
        if index == 2:
            spans = [[0, 5], [18, 21]]
        elif index in (3, 4):
            note, spans = 'note-2', [[5, 11]]
        elif index == 5:
            spans = [[6, 9]]
        elif index == 6:
            note, spans = 'note-3', [[0, 4]]
        encoded = texts[note].encode()
        masks.append(dict(short_id=f'V{index:03d}', vector_id=f'vector-{index}',
                          note_id=note, note_short_id='N00' + note[-1], byte_spans=spans,
                          fragments=[encoded[a:b].decode() for a, b in spans],
                          note_text_sha256=hashlib.sha256(encoded).hexdigest()))
    groups = ['coffee', 'tea', 'beans', 'drunk', 'flavour', 'chain']
    rows = []
    for group, title in zip(groups, TITLES):
        unique = {}
        for mask in masks:
            premise = ' '.join(mask['fragments'])
            model_input = f'premise: {premise} hypothesis: This text is about {title}.'
            row = unique.setdefault(model_input, dict(
                id='M' + hashlib.sha256(model_input.encode()).hexdigest(),
                category_id=group, category_title=title, premise=premise,
                model_input=model_input, masks=[]))
            row['masks'].append(copy.deepcopy(mask))
        rows.extend(unique.values())
    scores = [dict(copy.deepcopy(row), entailment_score=(
        .9 if (row['category_id'], row['premise']) in
        {('beans', 'coffee'), ('drunk', 'café tea')} else
        .142 if row['premise'] == 'cof' else .01), predicted=False) for row in rows]
    base = dict(ids=['V001'] + [f'V{n:03d}' for n in range(7, 946)], byte_spans=[[6, 12]])
    own = dict(ids=['V002'], byte_spans=[[0, 5], [18, 21]])
    filler = [f'other-{n}' for n in range(53)]
    nodes = [dict(node_id='root', label='All notes', children=['coffee', 'tea', *filler],
                  note_ids=[], analysis='original')]
    nodes += [dict(node_id=key, label=title, children=groups[2:] if key == 'coffee' else [],
                   note_ids=['N001'], analysis='original') for key, title in zip(groups, TITLES)]
    nodes += [dict(node_id=key, label=key, children=['beans'] if key == 'other-0' else [],
                   note_ids=['N001'], analysis='original') for key in filler]
    instances = {node['node_id']: {'N001': copy.deepcopy([base, own] if
                  node['node_id'] in ('root', 'coffee') else [base])} for node in nodes}
    highlights = {key: {short: sorted({tuple(span) for item in items for span in item['byte_spans']})
                        for short, items in notes.items()} for key, notes in instances.items()}
    baseline = dict(schema_version=2, hierarchy_id='baseline',
                    source_sha256=hashlib.sha256(source).hexdigest(), root_node_id='root',
                    notes=[dict(note_id='note-1', note_short_id='N001')], nodes=nodes,
                    note_masks=json.loads(json.dumps(highlights)), mask_instances=instances)
    return dict(baseline=baseline, source=source, inputs=rows,
                reused=[row for row in scores if row['category_id'] in groups[:2]],
                scores=[row for row in scores if row['category_id'] in groups[2:]])


class TrueBranchCategoriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def run_cli(self, values, after_freeze=None):
        run = self.directory / 'TRUE14'
        (run / 'run').mkdir(parents=True, exist_ok=True)
        paths = {'inputs': run / 'inputs.json', 'baseline': self.directory / 'baseline.json',
                 'source': self.directory / 'source.json', 'reused': self.directory / 'reused.jsonl',
                 'scores': run / 'run/scores.jsonl'}
        for key, path in paths.items():
            value = values[key]
            if key == 'source':
                path.write_bytes(value)
            elif key in ('reused', 'scores'):
                path.write_text(''.join(json.dumps(row) + '\n' for row in value))
            else:
                path.write_text(json.dumps(value))
        new_inputs = [row for row in values['inputs'] if row['category_title'] in TITLES[2:]]
        plan = dict(experiment='TRUE14', threshold=.142, unique_inputs=len(values['inputs']),
                    reused_inputs=len(values['reused']), new_inputs=len(new_inputs),
                    preservation_sha256={str(paths[key]): hashlib.sha256(paths[key].read_bytes()).hexdigest()
                                         for key in ('baseline', 'source', 'reused')})
        (run / 'new-inputs.json').write_text(json.dumps(new_inputs))
        (run / 'plan.json').write_text(json.dumps(plan))
        frozen = {name: hashlib.sha256((run / name).read_bytes()).hexdigest()
                  for name in ('inputs.json', 'new-inputs.json', 'plan.json')}
        (run / 'frozen.json').write_text(json.dumps(frozen))
        score_hash = hashlib.sha256(paths['scores'].read_bytes()).hexdigest()
        (run / 'run/completion.json').write_text(json.dumps(dict(
            pairs=len(values['scores']), scores_sha256=score_hash)))
        (run / 'run/execution.json').write_text(json.dumps(dict(experiment='TRUE14',
            frozen_sha256=hashlib.sha256((run / 'frozen.json').read_bytes()).hexdigest(),
            inputs=len(new_inputs))))
        (run / 'verification.json').write_text(json.dumps(dict(experiment='TRUE14',
            cache_identity_matches=True, old_inputs=len(values['reused']), new_inputs=len(new_inputs),
            old_scores_unchanged=True, new_scores_sha256=score_hash, exact_coverage=True)))
        if after_freeze is not None:
            after_freeze(run, paths)
        before = {key: path.read_bytes() for key, path in paths.items()}
        result = subprocess.run([sys.executable, str(CODE / 'true_branch_categories.py'),
            '--run', str(run), '--baseline', str(paths['baseline']), '--source', str(paths['source']),
            '--reused-scores', str(paths['reused'])], capture_output=True, text=True)
        self.assertEqual(before, {key: path.read_bytes() for key, path in paths.items()})
        return result, run

    def test_cli_adds_only_accepted_new_child_masks_and_inherits_up_shared_dag(self):
        values = fixture()
        result, run = self.run_cli(values)
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads((run / 'categories.json').read_text())
        original = values['baseline']
        nodes = {node['node_id']: node for node in actual['nodes']}
        self.assertEqual(len(nodes), 60)
        for old in original['nodes']:
            new = nodes[old['node_id']]
            self.assertEqual((new['node_id'], new['label'], new['children']),
                             (old['node_id'], old['label'], old['children']))
            if old['node_id'] != 'beans':
                self.assertEqual(new['note_ids'], old['note_ids'])
        self.assertEqual(nodes['beans']['note_ids'], ['N001', 'N002'])
        self.assertEqual(actual['notes'], [dict(note_id='note-1', note_short_id='N001'),
                                          dict(note_id='note-2', note_short_id='N002')])
        addition = [dict(ids=['V003', 'V004'], byte_spans=[[5, 11]])]
        for key in ('beans', 'coffee', 'other-0', 'root'):
            self.assertEqual(actual['mask_instances'][key]['N002'], addition)
        for key in ('tea', 'drunk', 'flavour', 'chain', 'other-1'):
            self.assertNotIn('N002', actual['mask_instances'][key])
        self.assertEqual(actual['mask_instances']['drunk']['N001'][-1],
                         dict(ids=['V002'], byte_spans=[[0, 5], [18, 21]]))
        self.assertEqual(actual['mask_instances']['tea'], original['mask_instances']['tea'])
        self.assertFalse(any('V005' in mask['ids'] for notes in actual['mask_instances'].values()
                             for masks in notes.values() for mask in masks))
        changes = json.loads((run / 'membership-changes.json').read_text())
        self.assertEqual([(row['category_id'], row['ids']) for row in changes['additions']],
                         [('beans', ['V003', 'V004']), ('drunk', ['V002'])])
        manifest = json.loads((run / 'packaging-manifest.json').read_text())
        self.assertEqual(manifest['coverage']['mask_category_pairs'], 5670)
        self.assertEqual(manifest['threshold'], .142)
        for key in ('new_inputs', 'plan', 'frozen', 'verification', 'completion', 'execution'):
            path = Path(manifest['input_paths'][key])
            self.assertEqual(manifest['input_sha256'][key], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_cli_requires_successful_verification(self):
        result, run = self.run_cli(fixture(), lambda run, paths: (run / 'verification.json').unlink())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('verification', result.stderr)
        self.assertFalse((run / 'categories.json').exists())

    def test_cli_refuses_finite_score_tampering_after_verification(self):
        def tamper(run, paths):
            rows = [json.loads(line) for line in paths['scores'].read_text().splitlines()]
            rows[0]['entailment_score'] = .91
            paths['scores'].write_text(''.join(json.dumps(row) + '\n' for row in rows))

        result, run = self.run_cli(fixture(), tamper)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('score checksum', result.stderr)
        self.assertFalse((run / 'categories.json').exists())

    def test_cli_refuses_incomplete_or_stale_run_provenance(self):
        for filename, field, value, expected in (
            ('verification.json', 'cache_identity_matches', False, 'successful TRUE14 verification'),
            ('verification.json', 'exact_coverage', False, 'successful TRUE14 verification'),
            ('verification.json', 'old_scores_unchanged', False, 'successful TRUE14 verification'),
            ('verification.json', 'new_scores_sha256', 'changed', 'score checksum'),
            ('run/completion.json', 'scores_sha256', 'changed', 'score checksum'),
            ('run/execution.json', 'frozen_sha256', 'changed', 'completed execution'),
            ('frozen.json', 'inputs.json', 'changed', 'frozen input changed'),
            ('plan.json', 'threshold', .5, 'frozen input changed')):
            with self.subTest(filename=filename, field=field):
                def tamper(run, paths):
                    path = run / filename
                    value_before = json.loads(path.read_text())
                    value_before[field] = value
                    path.write_text(json.dumps(value_before))

                result, run = self.run_cli(fixture(), tamper)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertFalse((run / 'categories.json').exists())

    def test_cli_refuses_partial_or_changed_evidence_without_writing_outputs(self):
        for case, expected in (
            ('missing_alias', 'all 945'), ('missing_score', 'scores must cover'),
            ('duplicate_score', 'duplicate scored'), ('score_metadata', 'score metadata'),
            ('changed_source', 'source checksum'), ('fragments', 'original source bytes'),
            ('alias_identity', 'original mask alias provenance'), ('model_input', 'model input'),
            ('nan', 'finite entailment'), ('cycle', 'cycle'),
            ('missing_category', 'all 59'), ('mask_ids', 'individual mask aliases'),
            ('highlights', 'individual masks differ')):
            with self.subTest(case=case):
                values = fixture()
                if case == 'missing_alias':
                    for row in [*values['inputs'], *values['scores'], *values['reused']]:
                        if row['category_id'] == 'beans':
                            row['masks'] = [mask for mask in row['masks'] if mask['short_id'] != 'V945']
                elif case == 'missing_score':
                    values['scores'].pop()
                elif case == 'duplicate_score':
                    values['scores'].append(copy.deepcopy(values['scores'][0]))
                elif case == 'score_metadata':
                    values['scores'][0]['masks'][0]['vector_id'] = 'wrong'
                elif case == 'changed_source':
                    values['source'] += b' '
                elif case == 'fragments':
                    values['inputs'][0]['masks'][0]['fragments'] = ['wrong']
                elif case == 'alias_identity':
                    values['inputs'][-1]['masks'][0]['vector_id'] = 'wrong'
                elif case == 'model_input':
                    values['inputs'][0]['model_input'] += ' '
                elif case == 'nan':
                    values['scores'][0]['entailment_score'] = float('nan')
                elif case == 'cycle':
                    values['baseline']['nodes'][3]['children'] = ['coffee']
                elif case == 'missing_category':
                    values['baseline']['nodes'].pop()
                elif case == 'mask_ids':
                    values['baseline']['mask_instances']['beans']['N001'][0]['ids'] = ['V002']
                elif case == 'highlights':
                    values['baseline']['note_masks']['beans']['N001'] = [[6, 9]]
                result, run = self.run_cli(values)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertFalse((run / 'categories.json').exists())
                self.assertFalse((run / 'membership-changes.json').exists())
                self.assertFalse((run / 'packaging-manifest.json').exists())

    def test_cli_never_replaces_packaged_evidence(self):
        values = fixture()
        result, run = self.run_cli(values)
        self.assertEqual(result.returncode, 0, result.stderr)
        paths = [run / name for name in ('categories.json', 'membership-changes.json', 'packaging-manifest.json')]
        before = [path.read_bytes() for path in paths]
        result, _ = self.run_cli(values)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('preserve existing packaging output', result.stderr)
        self.assertEqual(before, [path.read_bytes() for path in paths])

    def test_saved_true13_baseline_is_unchanged_when_no_new_child_mask_is_accepted(self):
        from true_branch_categories import expand

        research = CODE / 'navigation-research-v1'
        baseline_path = research / 'TRUE13/categories-with-mask-ids.json'
        source_path = CODE / 'real-note-fine-segmentation-v1/reviewed-input.json'
        score_path = research / 'TRUE12/scores.jsonl'
        paths = (baseline_path, source_path, score_path)
        before = [path.read_bytes() for path in paths]
        baseline = json.loads(before[0])
        reused = [json.loads(line) for line in before[2].splitlines()]
        input_fields = ('id', 'category_id', 'category_title', 'premise', 'model_input', 'masks')
        inputs = [{field: row[field] for field in input_fields} for row in reused]
        fresh = []
        for node in baseline['nodes']:
            if node['label'] not in TITLES[2:]:
                continue
            for old in reused:
                if old['category_title'] != 'Coffee':
                    continue
                row = {field: copy.deepcopy(old[field]) for field in input_fields}
                row.update(category_id=node['node_id'], category_title=node['label'])
                row['model_input'] = f'premise: {row["premise"]} hypothesis: This text is about {node["label"]}.'
                row['id'] = 'M' + hashlib.sha256(row['model_input'].encode()).hexdigest()
                inputs.append(row)
                fresh.append(dict(row, entailment_score=0.0, predicted=False))
        result, changes, coverage = expand(baseline, before[1], inputs, reused, fresh)
        self.assertEqual(before, [path.read_bytes() for path in paths])
        self.assertEqual(result['notes'], baseline['notes'])
        self.assertEqual(result['note_masks'], baseline['note_masks'])
        self.assertEqual(result['mask_instances'], baseline['mask_instances'])
        for old, new in zip(baseline['nodes'], result['nodes']):
            self.assertEqual({k: v for k, v in old.items() if k != 'analysis'},
                             {k: v for k, v in new.items() if k != 'analysis'})
        self.assertEqual(changes['additions'], [])
        self.assertEqual(coverage['source_notes'], 100)
        self.assertEqual(coverage['reachable_notes'], 79)
        self.assertEqual(coverage['scored_inputs'], 5388)


if __name__ == '__main__':
    unittest.main()
