"""Check the actual launcher and recompute the comparison's saved evidence."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "sse_multivector/manual-coffee-hierarchy-v1/m06-comparison.json"


class CoffeePreparationComparisonTest(unittest.TestCase):
    def test_launcher_from_another_directory_and_missing_binary(self):
        with tempfile.TemporaryDirectory(prefix="coffee comparison ") as directory:
            root = Path(directory)
            script = root / "sse_multivector/run-coffee-preparation-comparison.sh"
            script.parent.mkdir()
            shutil.copy2(ROOT / script.relative_to(root), script)
            binary = root / "target/merge-rule-review-build/debug/sse-subject-navigation"
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            result = subprocess.run([str(script), "--check"], cwd="/tmp", capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                "--compare",
                str(root / "sse_multivector/manual-coffee-hierarchy-v1/m06-comparison.json"),
                "--check",
            ])
            binary.unlink()
            result = subprocess.run([str(script)], cwd="/tmp", capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nix develop", result.stderr)

    def test_evidence_against_frozen_merge_history_and_all_aliases(self):
        manifest = json.loads(MANIFEST.read_text())
        evidence = manifest["evidence"]
        inputs = {}
        for key, expected in manifest["input_sha256"].items():
            data = (MANIFEST.parent / manifest[key]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, key)
            inputs[key] = json.loads(data)
        vectors = {v["vector_id"]: v for v in inputs["vector_map"]["vectors"]}
        history = inputs["merge_history"]
        aliases = history["alias_groups"]
        self.assertEqual(len(aliases), history["vector_count"])
        self.assertEqual(sorted(v for group in aliases for v in group), sorted(vectors))
        original_ids = {i: set(group) for i, group in enumerate(aliases)}
        point_ids = {i: {i} for i in range(len(aliases))}
        parent = {}
        for row in history["merges"]:
            group, left, right = row["id"], row["left"], row["right"]
            original_ids[group] = original_ids[left] | original_ids[right]
            point_ids[group] = point_ids[left] | point_ids[right]
            parent[left] = parent[right] = group
        note_ids = {g: {vectors[v]["note_short_id"] for v in ids}
                    for g, ids in original_ids.items()}
        short_ids = {g: {vectors[v]["short_id"] for v in ids}
                     for g, ids in original_ids.items()}
        roots = set(original_ids) - set(parent)
        self.assertEqual(len(roots), 1)
        root = roots.pop()
        for group, expected in evidence["groups"].items():
            group = int(group)
            self.assertEqual(sorted(note_ids[group]), expected["note_ids"])
            self.assertEqual(sorted(short_ids[group]), expected["vector_ids"])
            self.assertEqual(len(point_ids[group]), expected["canonical_vector_count"])
            self.assertEqual(len(original_ids[group]), expected["original_mask_count"])
            for minimum in (2, 5):
                displayed = group == root or (len(note_ids[group]) >= minimum
                            and note_ids[group] != note_ids[parent[group]])
                self.assertEqual(displayed, expected[f"displayed_minimum_{minimum}"])
        targets = set(evidence["target_note_ids"])
        all_mask_cover = min((g for g in original_ids if targets <= note_ids[g]),
                             key=lambda g: (len(note_ids[g]), len(point_ids[g])))
        self.assertEqual(all_mask_cover, evidence["smallest_raw_group_with_any_mask_per_target_note"])
        qualifying = evidence["preparation_mask_ids"]
        self.assertEqual(set(qualifying), targets)
        for note, ids in qualifying.items():
            self.assertTrue(ids)
            for vector in ids:
                matched = [v for v in vectors.values() if v["short_id"] == vector]
                self.assertEqual(len(matched), 1)
                self.assertEqual(matched[0]["note_short_id"], note)
        qualified_cover = min((g for g, ids in short_ids.items()
                               if all(ids.intersection(q) for q in qualifying.values())),
                              key=lambda g: (len(note_ids[g]), len(point_ids[g])))
        self.assertEqual(qualified_cover, evidence["smallest_raw_group_with_preparation_mask_per_target_note"])
        self.assertEqual(note_ids[qualified_cover], note_ids[evidence["displayed_group_with_same_notes"]])
        self.assertEqual(len(note_ids[qualified_cover]), 19)
        prep = next(n for n in inputs["manual_hierarchy"]["nodes"] if n["node_id"] == "coffee-preparation")
        self.assertEqual(set(prep["note_ids"]), targets)
        for page in manifest["pages"]:
            if page["kind"] == "merge":
                self.assertTrue(evidence["groups"][str(page["group_id"])][f'displayed_minimum_{page["min_notes"]}'])


if __name__ == "__main__":
    unittest.main()
