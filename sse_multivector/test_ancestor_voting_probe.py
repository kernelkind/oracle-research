import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from sse_multivector.ancestor_voting_probe import prepare_case, score_case


def fixture():
    # Query Q has a parent P and a descendant D. Two other subjects support P.
    names = ["P", "Q", "D", "Neighbor", "Other neighbor", "Root", "Unrelated"]
    subjects = [dict(index=i, subject=name, note_short_id=f"N{i}", number="1")
                for i, name in enumerate(names)]
    vectors = [[0, 1], [1, 0], [1, .01], [1, .1], [1, .2], [-1, 0], [0, -1]]
    groups = [[i] for i in range(len(names))]
    edges = [[0, 1], [1, 2], [0, 3], [0, 4], [5, 0]]
    return subjects, vectors, groups, edges


class AncestorVotingTests(unittest.TestCase):
    def test_neighbors_vote_for_ancestors_not_themselves(self):
        args = fixture()
        original = copy.deepcopy(args)
        case = prepare_case(*args, query=1)
        result = score_case(case, k=2, decay=.5)
        ranked = {r["node"]: r for r in result["ranking"]}
        self.assertEqual(case["excluded_nodes"], [1, 2])
        self.assertEqual(case["known_parents"], [0])
        self.assertEqual(ranked[0]["vote_rank"], 1)
        self.assertAlmostEqual(ranked[5]["vote_score"], ranked[0]["vote_score"] / 2)
        self.assertEqual(ranked[3]["vote_score"], 0)
        self.assertEqual(ranked[3]["direct_rank"], 1)
        self.assertEqual(args, original)

    def test_duplicate_subjects_and_descendants_cannot_reveal_hidden_link(self):
        subjects, vectors, groups, edges = fixture()
        subjects += [dict(index=7, subject="Q"), dict(index=8, subject="D copy")]
        vectors += [[1, 0], [1, .01]]
        groups += [[7], [8]]
        edges += [[0, 7], [7, 8]]
        case = prepare_case(subjects, vectors, groups, edges, query=1)
        self.assertEqual(case["excluded_nodes"], [1, 2, 7, 8])
        self.assertTrue(all(n["subject"] not in {"Q", "D", "D copy"}
                            for n in case["neighbors"]))

    def test_repeated_wording_votes_once_and_multiple_parent_paths_survive(self):
        subjects, vectors, groups, edges = fixture()
        subjects.append(dict(index=7, subject="Neighbor"))
        vectors.append([1, .1])
        groups.append([7])
        edges += [[0, 7], [6, 7], [5, 6]]
        case = prepare_case(subjects, vectors, groups, edges, query=1)
        result = score_case(case, k=1, decay=.5)
        self.assertEqual(result["neighbors"][0]["nodes"], [3, 7])
        scores = {r["node"]: r["vote_score"] for r in result["ranking"]}
        self.assertAlmostEqual(scores[0], scores[6])
        self.assertAlmostEqual(scores[5], scores[0] / 2)

    def test_zero_support_does_not_get_a_vote_rank_or_placement(self):
        subjects, vectors, groups, _ = fixture()
        case = prepare_case(subjects, vectors, groups, [], query=1)
        result = score_case(case, k=10, decay=1)
        self.assertTrue(all(r["vote_rank"] is None for r in result["ranking"]))
        self.assertNotIn("accepted_parents", result)

    def test_ties_at_neighbor_limit_are_retained(self):
        subjects, vectors, groups, edges = fixture()
        vectors[4] = vectors[3]
        result = score_case(prepare_case(subjects, vectors, groups, edges, query=1), k=1, decay=1)
        self.assertEqual(len(result["neighbors"]), 2)

    def test_rejects_cycles_bad_partitions_and_bad_parameters(self):
        subjects, vectors, groups, edges = fixture()
        with self.assertRaisesRegex(ValueError, "cycle"):
            prepare_case(subjects, vectors, groups, edges + [[2, 0]], query=1)
        with self.assertRaisesRegex(ValueError, "partition"):
            prepare_case(subjects, vectors, groups + [[1]], edges, query=1)
        case = prepare_case(subjects, vectors, groups, edges, query=1)
        for k, decay in ((0, .5), (1, 0), (1, float("nan")), (1, 2)):
            with self.assertRaises(ValueError):
                score_case(case, k=k, decay=decay)

    def test_cli_uses_receipts_keeps_inputs_and_refuses_overwrite_or_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe, matching = root / "probe", root / "matching"
            worker = probe / "worker-result"
            worker.mkdir(parents=True)
            matching.mkdir()
            subjects, vectors, groups, edges = fixture()
            rows = []
            for s in subjects:
                digest = hashlib.sha256(s["subject"].encode()).hexdigest()
                s["encoding_id"] = digest[:16]
                rows.append(dict(note_id=digest, subject_id=digest[:16]))
            inputs = probe / "inputs.json"
            inputs.write_text(json.dumps(dict(subjects=subjects, edges=edges, posts=[{}])))
            raw = worker / "raw-vectors.f32le"
            raw.write_bytes(struct.pack("<" + "f" * (2 * len(vectors)), *(v for row in vectors for v in row)))
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            receipt = worker / "worker-receipt.json"
            receipt.write_text(json.dumps(dict(rows=rows, row_count=len(rows), dimensions=2,
                files={raw.name: {"sha256": sha(raw)}}, proposal_sha256=sha(inputs))))
            (matching / "results.json").write_text(json.dumps(dict(groups=groups, edges=edges)))
            (matching / "provenance.json").write_text(json.dumps(dict(
                protected_sha256={str(p): sha(p) for p in (inputs, raw, receipt)})))
            original = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            output = root / "run"
            command = [sys.executable, "-m", "sse_multivector.ancestor_voting_probe", "--probe", str(probe),
                       "--matching", str(matching), "--holdout", "N1:1", "--inspect", "N6:1",
                       "--k", "2", "--decay", ".5", "--output", str(output)]
            process = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(process.returncode, 0, process.stderr)
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["measurements"][0]["vote_top1"], 1)
            self.assertEqual(summary["inference_calls"], 0)
            self.assertEqual(summary["placements"], 0)
            report = json.loads((output / "results.json").read_text())
            self.assertEqual(report["original_edges"], edges)
            self.assertEqual(report["nodes"][1]["origins"], [subjects[1]])
            snapshot = {p: p.read_bytes() for p in output.iterdir()}
            again = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("FileExistsError", again.stderr)
            self.assertEqual(snapshot, {p: p.read_bytes() for p in output.iterdir()})
            self.assertEqual(original, {p: p.read_bytes() for p in original})
            raw.write_bytes(b"changed")
            command[-1] = str(root / "corrupt-run")
            corrupt = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertNotEqual(corrupt.returncode, 0)
            self.assertIn("protected input changed", corrupt.stderr)
            self.assertFalse((root / "corrupt-run").exists())


if __name__ == "__main__":
    unittest.main()
