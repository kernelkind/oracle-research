import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from source_phrase_construction import construct, support_view


def example(row, note, text, annotations):
    tokens = list(re.finditer(r"\w+|[^\w\s]", text))
    assert len(tokens) == len(annotations)
    words = [dict(id=i + 1, text=t.group(), lemma=lemma, upos=pos,
                  head=head, deprel=rel, start_char=t.start(), end_char=t.end())
             for i, (t, (lemma, pos, head, rel)) in enumerate(zip(tokens, annotations))]
    return (dict(row=row, note=note, subject=text, text=text, fragments=[text], alias_ids=[]),
            dict(row=row, subject=text, sentences=[words]))


class SourcePhraseConstructionTests(unittest.TestCase):
    def test_stages_preserve_head_and_internal_preposition(self):
        record, parse = example(0, 'N01', 'In old boats with red sails.', [
            ('in', 'ADP', 3, 'case'), ('old', 'ADJ', 3, 'amod'),
            ('boat', 'NOUN', 0, 'root'), ('with', 'ADP', 6, 'case'),
            ('red', 'ADJ', 6, 'amod'), ('sail', 'NOUN', 3, 'nmod'),
            ('.', 'PUNCT', 3, 'punct')])
        before = copy.deepcopy((record, parse))
        result = construct([record], [parse])
        nodes = {n['label']: n for n in result['nodes']}
        self.assertEqual(set(nodes), {'boats', 'old boats', 'old boats with red sails',
                                      'sails', 'red sails'})
        labels = {n['id']: n['label'] for n in result['nodes']}
        self.assertEqual({(labels[e['parent']], labels[e['child']]) for e in result['edges']},
                         {('boats', 'old boats'), ('old boats', 'old boats with red sails'),
                          ('sails', 'red sails')})
        occ = nodes['old boats with red sails']['occurrences'][0]
        self.assertEqual(occ['fragments'], ['old boats with red sails'])
        self.assertEqual(occ['word_ids'], [2, 3, 4, 5, 6])
        self.assertEqual((record, parse), before)

    def test_lemma_identity_and_distinct_note_support(self):
        a, pa = example(0, 'N01', 'Old boat', [('old', 'ADJ', 2, 'amod'), ('boat', 'NOUN', 0, 'root')])
        b, pb = example(1, 'N01', 'Old boats', [('old', 'ADJ', 2, 'amod'), ('boat', 'NOUN', 0, 'root')])
        c, pc = example(2, 'N02', 'Old boats', [('old', 'ADJ', 2, 'amod'), ('boat', 'NOUN', 0, 'root')])
        r = construct([a, b, c], [pa, pb, pc])
        self.assertEqual(len(r['nodes']), 2)
        self.assertTrue(all(n['notes'] == ['N01', 'N02'] for n in r['nodes']))
        self.assertTrue(all(len(n['occurrences']) == 3 for n in r['nodes']))
        self.assertEqual(len(r['edges'][0]['witnesses']), 3)
        self.assertEqual(construct([c, b, a], [pc, pb, pa]), r)

    def test_no_edges_from_cooccurrence_or_copular_relation(self):
        a, pa = example(0, 'N01', 'Tea is a beverage.', [
            ('tea', 'NOUN', 4, 'nsubj'), ('be', 'AUX', 4, 'cop'),
            ('a', 'DET', 4, 'det'), ('beverage', 'NOUN', 0, 'root'),
            ('.', 'PUNCT', 4, 'punct')])
        r = construct([a], [pa])
        self.assertEqual(r['edges'], [])
        self.assertEqual({n['label'] for n in r['nodes']}, {'Tea', 'beverage'})

    def test_named_unit_and_exact_discontinuous_fragments(self):
        a, pa = example(0, 'N01', 'Café Aurora', [
            ('café', 'PROPN', 0, 'root'), ('aurora', 'PROPN', 1, 'flat')])
        r = construct([a], [pa])
        # The dependent is still a separate proposed head; no hidden semantic repair.
        full = next(n for n in r['nodes'] if n['label'] == 'Café Aurora')
        self.assertEqual(full['occurrences'][0]['fragments'], ['Café Aurora'])
        b, pb = example(1, 'N02', 'Boats, unusually, with sails', [
            ('boat', 'NOUN', 0, 'root'), (',', 'PUNCT', 1, 'punct'),
            ('unusually', 'ADV', 1, 'advmod'), (',', 'PUNCT', 1, 'punct'),
            ('with', 'ADP', 6, 'case'), ('sail', 'NOUN', 1, 'nmod')])
        r = construct([b], [pb])
        full = next(n for n in r['nodes'] if n['label'] == 'Boats with sails')
        self.assertEqual(full['occurrences'][0]['fragments'], ['Boats', 'with sails'])

    def test_views_preserve_disconnected_and_equal_note_choices(self):
        a, pa = example(0, 'N01', 'Old boats', [('old', 'ADJ', 2, 'amod'), ('boat', 'NOUN', 0, 'root')])
        b, pb = example(1, 'N02', 'Old boats', [('old', 'ADJ', 2, 'amod'), ('boat', 'NOUN', 0, 'root')])
        r = construct([a, b], [pa, pb])
        view = support_view(r, 2)
        self.assertEqual(len(view['node_ids']), 2)
        self.assertEqual(len(view['edges']), 1)
        self.assertEqual(len(view['equal_note_edges']), 1)
        self.assertEqual(support_view(r, 5)['node_ids'], [])

    def test_support_view_keeps_disconnected_retained_roots(self):
        result = dict(nodes=[dict(id='parent', notes=['N01', 'N02']),
                             dict(id='child', notes=['N01', 'N02']),
                             dict(id='isolated', notes=['N03', 'N04']),
                             dict(id='excluded', notes=['N05'])],
                      edges=[dict(parent='parent', child='child')])
        before = copy.deepcopy(result)
        view = support_view(result, 2)
        self.assertEqual(view['node_ids'], ['child', 'isolated', 'parent'])
        self.assertEqual(view['roots'], ['isolated', 'parent'])
        self.assertEqual(view['edges'], [dict(parent='parent', child='child')])
        self.assertEqual(result, before)

    def test_support_view_contracts_only_excluded_intermediates(self):
        result = dict(nodes=[dict(id='parent', notes=['N01', 'N02']),
                             dict(id='middle1', notes=['N01']),
                             dict(id='middle2', notes=['N01']),
                             dict(id='child', notes=['N01', 'N03']),
                             dict(id='excluded_leaf', notes=['N01'])],
                      edges=[dict(parent='parent', child='middle1'),
                             dict(parent='middle1', child='middle2'),
                             dict(parent='middle2', child='child'),
                             dict(parent='middle1', child='excluded_leaf')])
        before = copy.deepcopy(result)
        view = support_view(result, 2)
        self.assertEqual(view['node_ids'], ['child', 'parent'])
        self.assertEqual(view['roots'], ['parent'])
        self.assertEqual(view['edges'], [dict(parent='parent', child='child')])
        self.assertEqual(result, before)

    def test_support_view_stops_contraction_at_retained_intermediate(self):
        result = dict(nodes=[dict(id='parent', notes=['N01', 'N02']),
                             dict(id='middle', notes=['N01', 'N02']),
                             dict(id='excluded', notes=['N01']),
                             dict(id='child', notes=['N01', 'N03'])],
                      edges=[dict(parent='parent', child='middle'),
                             dict(parent='middle', child='excluded'),
                             dict(parent='excluded', child='child')])
        before = copy.deepcopy(result)
        view = support_view(result, 2)
        self.assertEqual(view['node_ids'], ['child', 'middle', 'parent'])
        self.assertEqual(view['roots'], ['parent'])
        self.assertEqual(view['edges'], [dict(parent='middle', child='child'),
                                         dict(parent='parent', child='middle')])
        self.assertNotIn(dict(parent='parent', child='child'), view['edges'])
        self.assertEqual(result, before)

    def test_validation_rejects_misalignment_offsets_and_cycles(self):
        a, pa = example(0, 'N01', 'Boat', [('boat', 'NOUN', 0, 'root')])
        bad = copy.deepcopy(pa)
        bad['subject'] = 'Ship'
        with self.assertRaises(ValueError):
            construct([a], [bad])
        bad = copy.deepcopy(pa)
        bad['sentences'][0][0]['end_char'] = 3
        with self.assertRaises(ValueError):
            construct([a], [bad])
        bad = copy.deepcopy(pa)
        bad['sentences'][0][0]['head'] = 1
        with self.assertRaises(ValueError):
            construct([a], [bad])
        with self.assertRaises(ValueError):
            construct([a, a], [pa, pa])

    def test_cli_uses_saved_production_parses_and_refuses_overwrite(self):
        a, pa = example(0, 'N01', 'Old boats', [('old', 'ADJ', 2, 'amod'), ('boat', 'NOUN', 0, 'root')])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, parses, output = root / 'source.json', root / 'parses.json', root / 'out'
            source.write_text(json.dumps([a]))
            parses.write_text(json.dumps([pa]))
            cmd = [sys.executable, str(Path(__file__).with_name('source_phrase_construction.py')),
                   '--input', str(source), '--parses', str(parses), '--output', str(output)]
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(json.loads((output / 'result.json').read_text()), construct([a], [pa]))
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
