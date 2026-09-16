"""Individual mask IDs are recovered from saved membership evidence, not highlights."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


CODE = Path(__file__).resolve().parent


def fixture():
    text = 'café coffee milk tea'
    source = json.dumps(dict(notes=[dict(note_id='full-note', text=text)]),
                        ensure_ascii=False).encode()

    def mask(identifier, spans):
        return dict(short_id=identifier, vector_id='vector-' + identifier,
                    note_id='full-note', note_short_id='N001', byte_spans=spans,
                    fragments=[text.encode()[a:b].decode() for a, b in spans],
                    note_text_sha256=hashlib.sha256(text.encode()).hexdigest())

    def score(identifier, spans, value):
        item = mask(identifier, spans)
        return dict(id='score-' + identifier, category_id='coffee', category_title='Coffee',
                    entailment_score=value, masks=[item],
                    model_input='premise: ' + ' '.join(item['fragments'])
                    + ' hypothesis: This text is about Coffee.')

    coffee = mask('V001', [[6, 12]])
    child = mask('V002', [[13, 17]])
    native = dict(nodes=[dict(group=group, title=title, matched_instances=[dict(
        instance=item['short_id'], vector_id=item['vector_id'], note_id=item['note_id'],
        byte_spans=item['byte_spans'], fragments=item['fragments'], text=text)])
        for group, title, item in [('coffee', 'Coffee', coffee), ('child', 'Milk', child)]
        ] + [dict(group='other', title='Other', matched_instances=[])])
    addition = score('V003', [[0, 5], [18, 21]], .9)
    addition['masks'].append(mask('V004', [[0, 5], [18, 21]]))
    scores = [addition, score('V005', [[6, 9]], .142),
              score('V001', [[6, 12]], .01)]
    all_spans = [[0, 5], [6, 12], [13, 17], [18, 21]]
    categories = dict(schema_version=2, hierarchy_id='fixture',
        source_sha256=hashlib.sha256(source).hexdigest(), root_node_id='root',
        notes=[dict(note_id='full-note', note_short_id='N001')],
        nodes=[dict(node_id='root', label='All notes', note_ids=[], children=['coffee', 'other']),
               dict(node_id='coffee', label='Coffee', note_ids=['N001'], children=['child']),
               dict(node_id='other', label='Other', note_ids=[], children=['child']),
               dict(node_id='child', label='Milk', note_ids=['N001'], children=[])],
        note_masks={'root': {'N001': all_spans}, 'coffee': {'N001': all_spans},
                    'other': {'N001': [[13, 17]]}, 'child': {'N001': [[13, 17]]}})
    return dict(categories=categories, native_notes=native, scores=scores, source=source)


class CategoryMaskInstancesTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_cli(self, values):
        paths = {}
        for name in ('categories', 'native_notes', 'scores', 'source'):
            path = self.root / (name + '.json')
            value = values[name]
            if name == 'source':
                path.write_bytes(value)
            elif name == 'scores':
                path.write_text(''.join(json.dumps(row) + '\n' for row in value))
            else:
                path.write_text(json.dumps(value))
            paths[name] = path
        before = {name: path.read_bytes() for name, path in paths.items()}
        output = self.root / 'enriched.json'
        args = [sys.executable, str(CODE / 'category_mask_instances.py')]
        for name, path in paths.items():
            args.extend(['--' + name.replace('_', '-'), str(path)])
        args.extend(['--output', str(output)])
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(before, {name: path.read_bytes() for name, path in paths.items()})
        return result, output

    def test_cli_keeps_individual_multispan_masks_and_alias_ids(self):
        values = fixture()
        result, output = self.run_cli(values)
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(output.read_text())
        masks = actual.pop('mask_instances')
        self.assertEqual(actual, values['categories'])
        expected = [dict(ids=['V001'], byte_spans=[[6, 12]]),
                    dict(ids=['V002'], byte_spans=[[13, 17]]),
                    dict(ids=['V003', 'V004'], byte_spans=[[0, 5], [18, 21]])]
        self.assertEqual(masks['coffee']['N001'], expected)
        self.assertEqual(masks['root']['N001'], expected)
        self.assertEqual(masks['other']['N001'], expected[1:2])
        self.assertEqual(masks['child']['N001'], expected[1:2])

    def test_cli_refuses_missing_evidence_or_changed_source(self):
        for case in ('missing', 'fragments', 'source', 'identity', 'cycle'):
            with self.subTest(case=case):
                values = fixture()
                if case == 'missing':
                    values['scores'][0]['entailment_score'] = .142
                elif case == 'fragments':
                    values['scores'][0]['masks'][0]['fragments'][0] = 'wrong'
                elif case == 'source':
                    values['source'] += b' '
                elif case == 'identity':
                    values['scores'][0]['masks'][0]['short_id'] = 'V001'
                else:
                    values['categories']['nodes'][-1]['children'] = ['coffee']
                result, output = self.run_cli(values)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())

    def test_cli_never_replaces_an_existing_output(self):
        result, output = self.run_cli(fixture())
        self.assertEqual(result.returncode, 0, result.stderr)
        before = output.read_bytes()
        result, output = self.run_cli(fixture())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), before)

    def test_native_membership_keeps_all_identical_mask_alias_ids(self):
        values = fixture()
        alias = copy.deepcopy(values['scores'][-1]['masks'][0])
        alias.update(short_id='V006', vector_id='vector-V006')
        values['scores'][-1]['masks'].append(alias)
        result, output = self.run_cli(values)
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(output.read_text())['mask_instances']['coffee']['N001']
        self.assertEqual(actual[0], dict(ids=['V001', 'V006'], byte_spans=[[6, 12]]))

    def test_actual_true13_reconstructs_identically_and_keeps_13_coffee_own_notes(self):
        from category_mask_instances import package

        research = CODE / 'navigation-research-v1'
        paths = [research / 'TRUE13/categories.json', research / 'TRUE13/native-notes.json',
                 research / 'TRUE12/scores.jsonl',
                 CODE / 'real-note-fine-segmentation-v1/reviewed-input.json']
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        actual = package(*paths, self.root / 'actual.json')
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths])
        self.assertEqual(actual, json.loads(
            (research / 'TRUE13/categories-with-mask-ids.json').read_text()))
        original = json.loads(paths[0].read_text())
        without_masks = copy.deepcopy(actual)
        masks = without_masks.pop('mask_instances')
        self.assertEqual(without_masks, original)
        for category, notes in masks.items():
            combined = {short: sorted({tuple(span) for mask in instances
                                       for span in mask['byte_spans']})
                        for short, instances in notes.items()}
            self.assertEqual(combined, {short: sorted(map(tuple, spans))
                                       for short, spans in original['note_masks'][category].items()})

        nodes = {node['node_id']: node for node in actual['nodes']}
        coffee = 'S9c440e7f47'

        def recursive_notes(key):
            result = set(nodes[key]['note_ids'])
            for child in nodes[key]['children']:
                result.update(recursive_notes(child))
            return result

        descendants = set()
        for child in nodes[coffee]['children']:
            descendants.update(recursive_notes(child))
        own = set(nodes[coffee]['note_ids']) - descendants
        self.assertEqual(sorted(own), ['N004', 'N018', 'N029', 'N035', 'N036', 'N041', 'N043',
                                     'N045', 'N048', 'N058', 'N060', 'N065', 'N079'])
        self.assertEqual(sum(len(masks[coffee][note]) for note in own), 41)
        self.assertEqual(sum(len(mask['ids']) for note in own for mask in masks[coffee][note]), 43)
        self.assertEqual(masks[coffee]['N004'], [
            dict(ids=['V034'], byte_spans=[[0, 5], [6, 18]]),
            dict(ids=['V036'], byte_spans=[[25, 50]])])
        self.assertEqual(masks[coffee]['N045'][0],
                         dict(ids=['V355', 'V356'], byte_spans=[[15, 26], [44, 61]]))


if __name__ == '__main__':
    unittest.main()
