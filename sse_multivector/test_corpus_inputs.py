"""Referenced corpora use the production experiment preparation and collection paths."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sse_multivector import experiment_inputs, hierarchy_inputs


class CorpusInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.notes = [dict(note_id="a" * 64, text="Tea {POST}", provenance={"rank": 1}),
                      dict(note_id="b" * 64, text="Music é", pubkey="original")]
        for name, note in zip(("food.json", "music.json"), self.notes):
            self.write(name, dict(schema_version=1, notes=[note]))
        self.path = self.write("source.json", dict(schema_version=1, sources=["food.json", "music.json"]))

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return path

    def prepare(self):
        return experiment_inputs.prepare_file(dict(adapter="subjects"), self.path, "Post: {POST}")

    def test_referenced_corpora_preserve_order_text_fields_and_hashes_through_collection(self):
        cases, hashes, _ = self.prepare()
        self.assertEqual([c["id"] for c in cases], [n["note_id"] for n in self.notes])
        self.assertEqual([c["inputs"]["POST"] for c in cases], [n["text"] for n in self.notes])
        for name in ("source.json", "food.json", "music.json"):
            path = self.root / name
            self.assertEqual(hashes[str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        plan = dict(dataset=dict(path=str(self.path)), sources=hashes,
                    experiment="SP", prompt=dict(id="ASv6.100"), runner={})
        entries = [dict(number="1", context="Source context", subject="Subject")]
        report = dict(cases=[dict(**c, parsed=dict(subjects=entries), receipt={}) for c in cases])
        collected = hierarchy_inputs.collect_subjects([(plan, report)])["subjects.json"]["notes"]
        for original, actual in zip(self.notes, collected):
            self.assertEqual({key: actual[key] for key in original}, original)

    def test_duplicate_note_identity_is_refused_even_with_same_text(self):
        for text in (self.notes[0]["text"], "conflicting text"):
            self.write("music.json", dict(schema_version=1, notes=[dict(note_id="a" * 64, text=text)]))
            with self.assertRaisesRegex(ValueError, "duplicate post identity"):
                self.prepare()

    def test_changed_referenced_source_is_refused_by_collection(self):
        _, hashes, _ = self.prepare()
        self.write("music.json", dict(schema_version=1, notes=[dict(note_id="b" * 64, text="changed")]))
        with self.assertRaisesRegex(ValueError, "protected source changed"):
            hierarchy_inputs.source_posts(dict(dataset=dict(path=str(self.path)), sources=hashes), {})

    def test_duplicate_source_reference_is_refused(self):
        self.write("source.json", dict(schema_version=1, sources=["food.json", "./food.json"]))
        with self.assertRaisesRegex(ValueError, "duplicate post source path"):
            self.prepare()
