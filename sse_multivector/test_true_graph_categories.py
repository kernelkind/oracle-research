"""The category viewer preserves saved TRUE routes, notes and branch-local masks."""
import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from true_category_graph import build_graph, prepare_inputs
from true_graph_notes import derive_note_memberships
from true_graph_categories import export


def fixture():
    texts = {'one': 'café coffee milk tea', 'two': 'bread'}
    values = [('A', 'one', 'coffee'), ('B', 'two', 'bread'),
              ('C', 'one', 'milk'), ('D', 'one', 'tea')]
    groups, packets, vectors = [], [], []
    for key, note, phrase in values:
        start = texts[note].encode().index(phrase.encode())
        instance = dict(instance='V'+key, fragments=[phrase])
        groups.append(dict(group=key, title=key, instances=[instance]))
        packets.append(dict(packet=key, instances=[dict(
            instance, note_id=note, text=texts[note], vector_id='vector-'+key,
            byte_spans=[[start, start+len(phrase.encode())]])]))
        vectors.append(dict(note_id=note, note_short_id='N001' if note == 'one' else 'N002'))
    titles = dict(groups=groups)
    scores = prepare_inputs(titles)
    for row in scores:
        yes = (row['a_id'], row['b_id']) in {('A', 'C'), ('B', 'C'), ('B', 'D')}
        row.update(entailment_score=0.9 if yes else 0.1, threshold_predicted=yes,
                   predicted=yes, generated_text='1' if yes else '0', eos_terminated=True,
                   generated_token_ids=[0, 209, 1] if yes else [0, 3, 632, 1])
    canonical = dict(titles=titles, scores=scores, source_packets=dict(packets=packets))
    graph = build_graph(titles, scores, decision_rule='native')
    return dict(canonical=canonical, graph=graph,
                memberships=derive_note_memberships(graph, canonical['source_packets']),
                source=dict(notes=[dict(note_id=k, text=t) for k, t in texts.items()]),
                mapping=dict(vectors=vectors))


class TrueGraphCategoriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_export(self, values):
        paths = []
        for name in ('canonical', 'graph', 'memberships', 'source', 'mapping'):
            path = self.root/(name+'.json')
            path.write_text(json.dumps(values[name], ensure_ascii=False))
            paths.append(path)
        before = {p: p.read_bytes() for p in paths}
        out = self.root/'categories.json'
        export(*paths, out, hierarchy_id='TRUE-test')
        self.assertEqual(before, {p: p.read_bytes() for p in paths})
        return json.loads(out.read_text())

    def test_shared_child_and_original_ids_titles_notes_are_preserved(self):
        spec = self.run_export(fixture())
        self.assertEqual(spec['schema_version'], 2)
        nodes = {n['node_id']: n for n in spec['nodes']}
        self.assertEqual(set(nodes), {'root', 'A', 'B', 'C', 'D'})
        self.assertEqual(nodes['root']['children'], ['A', 'B'])
        self.assertEqual(nodes['A']['children'], ['C'])
        self.assertEqual(nodes['B']['children'], ['C', 'D'])
        self.assertEqual(nodes['A']['label'], 'A')
        self.assertEqual(nodes['C']['label'], 'C')
        self.assertEqual(nodes['A']['note_ids'], ['N001'])
        self.assertEqual(nodes['B']['note_ids'], ['N002'])
        self.assertEqual(spec['notes'], [dict(note_id='one', note_short_id='N001'),
                                         dict(note_id='two', note_short_id='N002')])
        self.assertEqual(spec['source_sha256'], hashlib.sha256(
            (self.root/'source.json').read_bytes()).hexdigest())

    def test_masks_include_all_descendants_but_not_sibling_masks_of_the_same_note(self):
        spec = self.run_export(fixture())
        masks = spec['note_masks']
        self.assertEqual(masks['A'], {'N001': [[6, 12], [13, 17]]})
        self.assertEqual(masks['B'], {'N001': [[13, 17], [18, 21]], 'N002': [[0, 5]]})
        self.assertEqual(masks['C'], {'N001': [[13, 17]]})
        self.assertEqual(masks['root'], {'N001': [[6, 12], [13, 17], [18, 21]],
                                         'N002': [[0, 5]]})

    def test_changed_graph_memberships_source_or_short_ids_are_rejected(self):
        for case in range(5):
            with self.subTest(case=case):
                values = fixture()
                if case == 0:
                    values['graph']['transitive_reduced_edges'].pop()
                elif case == 1:
                    values['memberships']['nodes'][0]['recursive_note_ids'] = []
                elif case == 2:
                    values['source']['notes'][0]['text'] += ' modified'
                elif case == 3:
                    values['mapping']['vectors'][0]['note_short_id'] = 'N099'
                else:
                    for v in values['mapping']['vectors']:
                        v['note_short_id'] = 'N001'
                with self.assertRaises(ValueError):
                    self.run_export(values)
                self.assertFalse((self.root/'categories.json').exists())

    def test_existing_output_is_not_overwritten(self):
        self.run_export(fixture())
        out = self.root/'categories.json'
        before = out.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_export(fixture())
        self.assertEqual(out.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
