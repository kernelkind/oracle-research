"""Exercise the offline matching procedure, not a duplicate test algorithm."""
import math
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from sse_multivector.subject_matching_probe import match_subjects, browser_spec, run
from sse_multivector.subject_order_probe import build_inputs


def vector(angle):
    return [math.cos(angle), math.sin(angle)]


def inputs(posts, subjects=None, edges=()):
    return dict(subjects=[dict(index=i, note_id=p, note_short_id=p,
                              number=str(i + 1), subject=(subjects or posts)[i],
                              mask_vector_ids=[f"v{i}"], byte_spans=[[0, 1]], fragments=["x"])
                          for i, p in enumerate(posts)], edges=[list(e) for e in edges],
                posts=[dict(note_id=p, note_short_id=p, text="x") for p in sorted(set(posts))])


class SubjectMatchingTests(unittest.TestCase):
    def test_matches_both_levels_but_not_a_more_specific_subject(self):
        data = inputs(["A"] * 3 + ["B"] * 3,
                      ["Bread", "Sourdough bread", "Preparation", "Food", "Bread", "Sourdough bread"],
                      [(0, 1), (1, 2), (3, 4), (4, 5)])
        subjects = [vector(a) for a in (0, 1, 1.1, 2.5, 0, 1)]
        masks = subjects.copy()
        masks[3] = None
        result = match_subjects(data, subjects, masks)
        self.assertEqual(result["accepted_pairs"], [[0, 4], [1, 5]])
        self.assertEqual(result["groups"], [[0, 4], [1, 5], [2], [3]])
        self.assertEqual(result["edges"], [[0, 1], [1, 2], [3, 0]])
        self.assertEqual(result, match_subjects(data, subjects, masks))

    def test_mask_search_selects_posts_not_subject_similarity(self):
        data = inputs(["A", "B", "C"])
        result = match_subjects(data, [vector(0), vector(2), vector(0)],
                                [vector(0), vector(.1), vector(2)])
        self.assertEqual(result["candidate_post_pairs"], [["A", "B"], ["B", "C"]])
        self.assertNotIn([0, 2], [r["pair"] for r in result["comparisons"]])

    def test_best_choices_are_within_each_post_pair_and_chains_can_merge(self):
        data = inputs(["A", "B", "C"])
        vectors = [vector(a) for a in (0, .4, .8)]
        result = match_subjects(data, vectors, vectors)
        self.assertEqual(result["accepted_pairs"], [[0, 1], [1, 2]])
        self.assertEqual(result["groups"], [[0, 1, 2]])
        self.assertLess(math.cos(.8), .9)  # A/C would fail, but chains are approved.

    def test_mutual_choice_is_checked_before_thresholds_or_empty_mask_filter(self):
        data = inputs(["A", "B", "B"])
        subject_vectors = [vector(0), vector(0), vector(.1)]
        result = match_subjects(data, subject_vectors, [vector(0), None, vector(0)])
        self.assertEqual(result["accepted_pairs"], [])
        self.assertEqual(result["groups"], [[0], [1], [2]])
        decisions = {tuple(r["pair"]): r for r in result["comparisons"]}
        self.assertEqual(decisions[0, 1]["reason"], "empty-mask")
        self.assertEqual(decisions[0, 2]["reason"], "not-mutual")

    def test_both_cosine_thresholds_are_required(self):
        for subjects, masks, reason in [
            ([vector(0), vector(.6)], [vector(0), vector(0)], "subject-cutoff"),
            ([vector(0), vector(0)], [vector(0), vector(.8)], "mask-cutoff"),
        ]:
            result = match_subjects(inputs(["A", "B"]), subjects, masks)
            self.assertEqual(result["accepted_pairs"], [])
            self.assertEqual(result["comparisons"][0]["reason"], reason)

    def test_ties_remain_and_internal_sp_edge_may_collapse(self):
        data = inputs(["A", "B", "B"], edges=[(1, 2)])
        vectors = [vector(0)] * 3
        result = match_subjects(data, vectors, vectors)
        self.assertEqual(result["accepted_pairs"], [[0, 1], [0, 2]])
        self.assertEqual(result["groups"], [[0, 1, 2]])
        self.assertEqual(result["collapsed_sp_edges"], [[1, 2]])
        self.assertEqual(result["cycle_rollbacks"], [])

    def test_all_merges_in_cycle_are_undone_but_unrelated_merge_is_kept(self):
        data = inputs(["A", "A", "B", "B", "C", "D"], edges=[(0, 1), (2, 3)])
        vectors = [vector(a) for a in (0, 1.2, 1.2, 0, 2.8, 2.8)]
        result = match_subjects(data, vectors, vectors)
        self.assertEqual(result["accepted_pairs"], [[0, 3], [1, 2], [4, 5]])
        self.assertEqual(result["groups"], [[0], [1], [2], [3], [4, 5]])
        self.assertEqual(result["edges"], [[0, 1], [2, 3]])
        self.assertEqual(result["cycle_rollbacks"][0]["groups"], [[0, 3], [1, 2]])

    def test_no_mask_candidates_does_not_remove_subjects(self):
        result = match_subjects(inputs(["A", "B"]), [vector(0)] * 2, [None, None])
        self.assertEqual(result["candidate_post_pairs"], [])
        self.assertEqual(result["groups"], [[0], [1]])

    def test_invalid_vectors_and_original_cycles_are_rejected(self):
        for vectors in ([[0, 0], vector(0)], [[float("nan"), 0], vector(0)], [[1], [1, 0]]):
            with self.assertRaises(ValueError):
                match_subjects(inputs(["A", "B"]), vectors, vectors)
        with self.assertRaises(ValueError):
            match_subjects(inputs(["A", "A"], edges=[(0, 1), (1, 0)]),
                           [vector(0)] * 2, [vector(0)] * 2)

    def test_browser_keeps_empty_subject_source_and_each_original_mask_id(self):
        data = inputs(["A", "B", "A"], ["Name A", "Name B", "Empty"])
        data["subjects"][2].update(mask_vector_ids=[], byte_spans=[], fragments=[])
        masks = {f"v{i}": dict(vector_id=f"v{i}", short_id=f"V{i}", note_id=p,
                                 note_short_id=p, byte_spans=[[0, 1]], fragments=["x"])
                 for i, p in enumerate(["A", "B"])}
        result = match_subjects(data, [vector(0), vector(0), vector(2)],
                                [vector(0), vector(0), None])
        spec = browser_spec(data, result, masks, "source-hash")
        by_id = {n["node_id"]: n for n in spec["nodes"]}
        self.assertEqual(by_id["S0000"]["label"], "Name A / Name B")
        self.assertEqual(by_id["S0000"]["note_ids"], ["A", "B"])
        self.assertEqual(spec["mask_instances"]["S0000"]["A"][0]["ids"], ["V0"])
        self.assertEqual(spec["mask_instances"]["S0000"]["B"][0]["ids"], ["V1"])
        self.assertEqual(by_id["S0002"]["note_ids"], ["A"])
        self.assertEqual(spec["note_masks"]["S0002"], {"A": []})
        self.assertEqual(spec["mask_instances"]["S0002"], {"A": []})
        self.assertIn("empty mask", by_id["S0002"]["analysis"])


class SavedMatchingTests(unittest.TestCase):
    def fixture(self, directory):
        source, probe = directory / "source", directory / "probe"
        source.mkdir()
        probe.mkdir()

        def save(path, value):
            path.write_text(json.dumps(value))

        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()

        notes, mapping = [], []
        for i in (1, 2):
            note = str(i) * 64
            notes.append(dict(note_id=note, text="bread", subjects=[
                dict(number="1", subject="Bread", id=f"m{i}", byte_spans=[[0, 5]], fragments=["bread"]),
                dict(number="2", subject="Empty", id=f"e{i}", byte_spans=[], fragments=[])]))
            mapping.append(dict(note_id=note, note_short_id=f"N00{i}", vector_id=f"v{i}",
                                short_id=f"V{i}", worker_subject_id=f"m{i}",
                                byte_spans=[[0, 5]], fragments=["bread"]))
        save(source / "masked-posts.json", dict(notes=notes))
        save(source / "vector-map.json", dict(vectors=mapping))
        data, encodings = build_inputs(dict(notes=notes), dict(vectors=mapping), ["N001", "N002"])
        data["protected_sha256"] = {str(p): sha(p) for p in source.iterdir()}
        save(probe / "inputs.json", data)
        identity = dict(checkpoint_sha256="checkpoint", base_model_artifact_tree_sha256="model",
                        model="saved SSE", runtime={"test": True})

        def worker(folder, rows, vectors, proposal):
            folder.mkdir()
            path = folder / "raw-vectors.f32le"
            path.write_bytes(struct.pack("<" + "f" * (2 * len(vectors)), *(v for row in vectors for v in row)))
            save(folder / "worker-receipt.json", dict(identity, rows=rows, row_count=len(rows), dimensions=2,
                 files={path.name: {"sha256": sha(path)}}, proposal_sha256=proposal))

        worker(source / "worker-result", [dict(note_id=m["note_id"], subject_id=m["worker_subject_id"])
                                          for m in mapping], [[1, 0], [1, 0]], "mask-proposal")
        worker(probe / "worker-result", [dict(note_id=e["note_id"], subject_id=e["subjects"][0]["subject_id"])
                                         for e in encodings["notes"]], [[1, 0], [0, 1]], sha(probe / "inputs.json"))
        return source, probe

    def test_cli_reproduces_saved_inputs_without_mutating_or_overwriting_them(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source, probe = self.fixture(directory)
            before = {p: p.read_bytes() for folder in (source, probe) for p in folder.rglob("*") if p.is_file()}
            output = directory / "run"
            command = [sys.executable, "-m", "sse_multivector.subject_matching_probe", "--source", str(source),
                       "--probe", str(probe), "--output", str(output)]
            process = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(process.returncode, 0, process.stderr)
            summary = json.loads(process.stdout)
            self.assertEqual((summary["subjects"], summary["nodes"], summary["empty_masks"]), (4, 3, 2))
            self.assertEqual(summary["inference_calls"], 0)
            spec = json.loads((output / "categories.json").read_text())
            self.assertEqual(len(spec["nodes"]), 4)
            self.assertEqual(spec["mask_instances"]["S0000"]["N002"][0]["ids"], ["V2"])
            snapshot = {p: p.read_bytes() for p in output.iterdir()}
            again = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("FileExistsError", again.stderr)
            self.assertEqual(snapshot, {p: p.read_bytes() for p in output.iterdir()})
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_saved_vector_corruption_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source, probe = self.fixture(directory)
            (probe / "worker-result" / "raw-vectors.f32le").write_bytes(b"broken")
            with self.assertRaisesRegex(ValueError, "vector hash mismatch"):
                run(source, probe, directory / "run")
            self.assertFalse((directory / "run").exists())

    def test_changed_source_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source, probe = self.fixture(directory)
            path = source / "masked-posts.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "protected input changed"):
                run(source, probe, directory / "run")
            self.assertFalse((directory / "run").exists())


if __name__ == "__main__":
    unittest.main()
