"""Saved-source CLI audit: note presence must not hide omitted topics."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector import section_count_panel as panel


class GroupOmissionTests(unittest.TestCase):
    def test_cli_reports_omitted_topics_on_retained_and_missing_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            angles = np.array([0, .01, .3, 1, 1.01, 1.4, 2])
            # 0/1 and 3/4 are reciprocal; 2/5/6 stay independent.
            notes = ['a', 'b', 'a', 'c', 'd', 'e', 'f']
            np.savez(root / 'vectors.npz', vectors=np.c_[np.cos(angles), np.sin(angles)],
                     notes=np.array(notes))
            entries = [dict(id=str(i), title=t, meaning=t + ' meaning', note_id=n,
                            local_number=str(i + 1), source_group=None)
                       for i, (n, t) in enumerate(zip(notes, [
                           'Nostr', 'Nostr', 'Unique topic', 'Food', 'Food',
                           'Omitted topic', 'Another omitted topic']))]
            panel._write(root / 'entries.json', entries)
            corpus = dict(notes=[dict(note_id=n, text='post ' + n,
                                      origin=dict(prompt_version='ASv6.100'))
                                 for n in 'abcdefg'])
            panel._write(root / 'corpus.json', corpus)
            files = {str(p): panel._sha(p) for p in
                     [root / 'vectors.npz', root / 'entries.json', root / 'corpus.json']}
            source = dict(input=str(root / 'vectors.npz'), entries=str(root / 'entries.json'),
                          files=files)
            spec = dict(counts=[1], seeds=[1], max_iterations=5, time_limit=10,
                        sources=dict(source=source), cases=[dict(
                            id='All', source='source', role='development', minimum_notes=0,
                            selector=dict(kind='all'), preserve_groups=True, reciprocal_nearest=True)])
            panel._write(root / 'spec.json', spec)
            panel.prepare(root / 'spec.json', root / 'panel')
            manifest = dict(cases=[dict(id='Fixture', panel=str(root / 'panel/plan.json'),
                                       panel_sha256=panel._sha(root / 'panel/plan.json'),
                                       case='All', corpus=str(root / 'corpus.json'))])
            panel._write(root / 'audit.json', manifest)
            cli = [sys.executable, '-m', 'sse_multivector.section_group_omissions',
                   str(root / 'audit.json'), str(root / 'output')]
            result = subprocess.run(cli, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = panel._read(root / 'output/Fixture.json')
            self.assertEqual(report['counts']['corpus_notes'], 7)
            self.assertEqual(report['counts']['unavailable_notes'], 1)
            self.assertEqual(report['counts']['retained_notes'], 4)
            self.assertEqual(report['counts']['omitted_usable_notes'], 2)
            self.assertEqual(report['counts']['retained_notes_with_omissions'], 1)
            a = next(n for n in report['notes'] if n['note_id'] == 'a')
            self.assertEqual([e['title'] for e in a['retained']], ['Nostr'])
            self.assertEqual([e['title'] for e in a['omitted']], ['Unique topic'])
            self.assertEqual(a['text'], 'post a')
            self.assertEqual(report['wholly_omitted_titles']['Unique topic'], ['2'])
            original = (root / 'output/Fixture.json').read_bytes()
            again = subprocess.run(cli, text=True, capture_output=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual((root / 'output/Fixture.json').read_bytes(), original)
            (root / 'corpus.json').write_text('{}')
            changed = subprocess.run(cli[:-1] + [str(root / 'bad')], text=True, capture_output=True)
            self.assertNotEqual(changed.returncode, 0)
            self.assertIn('Frozen source changed', changed.stderr)


if __name__ == '__main__':
    unittest.main()
