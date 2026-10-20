"""Large saved sources stay hash-bound without loading discarded JSON values."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import ijson

from sse_multivector.historical_study_publication import Sources


class HistoricalStudyStreamsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / 'response.json'
        self.raw = json.dumps({'artifact': {'result': {
            'fine_output': {'segments': [{'id': 'group', 'members': ['subject']}]},
            'working_distances': [[0, 1], [1, 0]],
        }}}).encode()
        self.path.write_bytes(self.raw)
        self.metadata = {'sources': {}, 'exporter_sources': {}}
        self.sources = Sources(self.root, {'source': {
            'path': 'response.json', 'sha256': hashlib.sha256(self.raw).hexdigest(),
        }}, self.metadata)

    def test_nested_selected_values_and_complete_source_hash(self):
        with self.sources.stream('response.json') as stream:
            selected = list(ijson.items(stream, 'artifact.result.fine_output'))

        self.assertEqual(selected, [{'segments': [{'id': 'group', 'members': ['subject']}]}])
        self.assertEqual(self.metadata['sources']['response.json'],
                         hashlib.sha256(self.raw).hexdigest())
        self.assertIn('sse_multivector/numerical_publication.py',
                      self.metadata['exporter_sources'])
        self.sources.check()

    def test_short_read_still_hashes_discarded_tail(self):
        self.path.write_bytes(self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            with self.sources.stream('response.json') as stream:
                self.assertEqual(stream.read(1), b'{')

    def test_source_change_during_read_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'changed during export'):
            with self.sources.stream('response.json') as stream:
                stream.read(1)
                self.path.write_bytes(self.raw + b' ')

    def test_unselected_and_nonportable_paths_are_rejected(self):
        for name, message in [('other.json', 'not selected'),
                              ('../response.json', 'repository-relative')]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, message):
                    with self.sources.stream(name):
                        self.fail('unselected source opened')

    def test_end_check_detects_changes_after_stream_closes(self):
        with self.sources.stream('response.json') as stream:
            list(ijson.items(stream, 'artifact.result.fine_output'))
        self.path.write_bytes(self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'changed during export'):
            self.sources.check()
