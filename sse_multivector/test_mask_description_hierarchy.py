import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mask_description_hierarchy import descriptions_from_masks, description_relations


def evidence(pairs):
    return [dict(row=i, aliases=[dict(note_short_id=n, fragments=f)])
            for i, (n, f) in enumerate(pairs)]


class DescriptionHierarchyTests(unittest.TestCase):
    def test_note_containment_is_not_descriptor_extension(self):
        records = evidence([
            ('a', ['bread']), ('a', ['coffee']),
            ('b', ['sourdough bread']), ('b', ['coffee']),
            ('c', ['sourdough', 'bread']), ('c', ['coffee']),
            ('d', ['coffee']),
        ])
        ds = descriptions_from_masks(records, keep_symbols=True)
        by_words = {tuple(d['features']): d['id'] for d in ds}
        bread, coffee, sourdough = (by_words[w] for w in
                                   [('bread',), ('coffee',), ('bread', 'sourdough')])
        rel = description_relations(ds)
        self.assertIn([coffee, bread], rel['note_subset']['all_edges'])
        self.assertNotIn([coffee, bread], rel['descriptor_extension']['all_edges'])
        self.assertIn([bread, sourdough], rel['descriptor_extension']['immediate_edges'])

    def test_symbols_are_not_silently_erased_from_complete_mask(self):
        records = evidence([('a', ['I', '😴']), ('b', ['I', 'work'])])
        words = descriptions_from_masks(records, keep_symbols=False)
        symbols = descriptions_from_masks(records, keep_symbols=True)
        self.assertEqual([d['features'] for d in words], [['i']])
        self.assertEqual(symbols, [])

    def test_repetition_from_one_note_does_not_supply_second_note(self):
        self.assertEqual(descriptions_from_masks(evidence([
            ('a', ['bread']), ('a', ['bread']),
        ]), keep_symbols=True), [])

    def test_equal_note_sets_are_not_a_narrowing(self):
        ds = descriptions_from_masks(evidence([
            ('a', ['bread']), ('a', ['sourdough bread']),
            ('b', ['bread']), ('b', ['sourdough bread']),
        ]), keep_symbols=True)
        rel = description_relations(ds)
        self.assertEqual(rel['note_subset']['all_edges'], [])
        self.assertEqual(rel['descriptor_extension']['all_edges'], [])

    def test_only_immediate_edges_are_exposed(self):
        ds = descriptions_from_masks(evidence([
            ('a', ['bread']), ('b', ['sourdough bread']),
            ('c', ['rye sourdough bread']), ('d', ['rye sourdough bread']),
        ]), keep_symbols=True)
        rel = description_relations(ds)['descriptor_extension']
        self.assertEqual(len(rel['all_edges']), 3)
        self.assertEqual(len(rel['immediate_edges']), 2)

    def test_aliases_must_agree_on_source_note_and_features(self):
        for alternate in [dict(note_short_id='b', fragments=['bread']),
                          dict(note_short_id='a', fragments=['coffee'])]:
            records = evidence([('a', ['bread']), ('b', ['bread'])])
            records[0]['aliases'].append(alternate)
            with self.assertRaisesRegex(ValueError, 'aliases disagree'):
                descriptions_from_masks(records, keep_symbols=True)

    def test_cli_preserves_evidence_snapshots_and_previous_output(self):
        records = evidence([('a', ['bread']), ('b', ['sourdough bread']),
                            ('c', ['sourdough bread']), ('d', ['😴'])])
        script = Path(__file__).with_name('mask_description_hierarchy.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'evidence.json'
            source.write_text(json.dumps(records))
            output = root / 'result'
            command = [sys.executable, str(script), '--evidence', str(source),
                       '--output', str(output), '--run-id', 'test',
                       '--features', 'words-and-symbols']
            run = subprocess.run(command, text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(run.stdout)['covered_notes'], 3)
            config = json.loads((output / 'config.json').read_text())
            self.assertEqual(config['uncovered_notes'], ['d'])
            self.assertEqual(config['source']['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(json.loads((output / 'review.json').read_text()), records[:3])
            for name, digest in config['code_sha256'].items():
                self.assertEqual(hashlib.sha256((output / 'source' / name).read_bytes()).hexdigest(), digest)
            before = {str(p.relative_to(output)): p.read_bytes()
                      for p in output.rglob('*') if p.is_file()}
            rerun = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn('preserve earlier experiments', rerun.stderr)
            after = {str(p.relative_to(output)): p.read_bytes()
                     for p in output.rglob('*') if p.is_file()}
            self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
