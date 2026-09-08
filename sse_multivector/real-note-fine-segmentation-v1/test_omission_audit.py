import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omission_audit import _eligible, prepare, sample
from sse_multivector.real_note_segmentation import (
    NORMALIZATION,
    REVIEW_INSTRUCTIONS,
    REVIEW_QUESTION,
    REVIEW_VERDICTS,
    _canonical,
    _compile_inputs,
)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(value))


def read(path):
    return json.loads(path.read_text())


def identity(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def fixture(root):
    # Exactly the frozen accounting, with deliberately tied unit vectors.
    counts = [75, 75, 211, 211, 211] + [1] * 162
    notes = []
    for n, count in enumerate(counts, 1):
        notes.append({
            "note_id": f"{n:064x}",
            "text": "☕ coffee / coffee\nhttps://example.test/original  ",
            "subjects": [{"id": f"s{k}", "subject": "fixture only",
                          "judgment": "accepted", "fragments": ["☕", "coffee"],
                          "byte_spans": [[0, 3], [13, 19]]}
                         for k in range(count)],
        })
    reviewed = {"schema_version": 1, "notes": notes}
    vector_dir = root / "vectors"
    write(vector_dir / "reviewed-input.json", reviewed)
    _, mapping = _compile_inputs(reviewed, identity(vector_dir / "reviewed-input.json")["sha256"])
    mapping["dimensions"] = 2
    write(vector_dir / "vector-map.json", mapping)
    (vector_dir / "normalized-vectors.f64le").write_bytes(struct.pack("<2d", 1, 0) * 945)
    (vector_dir / "raw-vectors.f32le").write_bytes(struct.pack("<2f", 1, 0) * 945)
    write(vector_dir / "manifest.json", {
        "schema_version": 1, "dimensions": 2, "vector_count": 945,
        "raw_decode_and_normalization_contract": NORMALIZATION,
        "files": {name: identity(vector_dir / name) for name in (
            "reviewed-input.json", "vector-map.json", "normalized-vectors.f64le", "raw-vectors.f32le")},
    })
    instances = [{"instance": v["short_id"], "vector_id": v["vector_id"],
                  "note_id": v["note_id"], "text": notes[v["reviewed_note_index"]]["text"],
                  "byte_spans": v["byte_spans"]} for v in mapping["vectors"]]
    by_id = {i["instance"]: i for i in instances}

    def partition(name, groups):
        used = {v for group in groups for v in group}
        packets = [{"packet": "S" + hashlib.sha256(_canonical(sorted(by_id[v]["vector_id"] for v in group))).hexdigest()[:10],
                    "instances": [by_id[v] for v in group], "question": REVIEW_QUESTION,
                    "verdicts": REVIEW_VERDICTS} for group in groups]
        write(root / f"hdbscan-{name}/review/review.json", {
            "schema_version": 3, "review_set": "fixture", "instructions": REVIEW_INSTRUCTIONS,
            "response_contract": {}, "packets": packets})
        write(root / f"hdbscan-{name}/review/unassigned.json", {
            "schema_version": 1, "kind": "unassigned",
            "instances": [i for i in instances if i["instance"] not in used]})
        review_dir = root / f"hdbscan-{name}/review"
        write(review_dir / "manifest.json", {
            "schema_version": 1,
            "files": {name: identity(review_dir / name) for name in ("review.json", "unassigned.json")},
        })
    partition("baseline", [[f"V{k:03d}" for k in range(a, b)] for a, b in (
        (1, 151), (151, 362), (362, 573), (573, 784))])
    partition("leaf", [["V151", "V152", "V784", "V785"]])
    partition("density", [["V151", "V784", "V001", "V076"]])
    return by_id


class OmissionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.instances = fixture(cls.root / "source")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.output_dir = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.output_dir.cleanup)
        self.out = Path(self.output_dir.name)

    def prepared(self):
        output = self.out / "audit"
        prepare(self.root / "source", output)
        return output

    def test_prepare_accounts_eligibility_and_all_alternate_routes(self):
        audit = self.prepared()
        manifest = read(audit / "manifest.json")
        self.assertEqual({"total": 945, "baseline_multi_note": 150,
                          "baseline_one_note": 633, "baseline_noise": 162,
                          "excluded": 795}, manifest["accounting"])
        excluded = read(audit / "excluded-ids.json")
        self.assertEqual([f"V{k:03d}" for k in range(151, 946)], excluded)
        pairs = {tuple(p["pair"]): p for p in read(audit / "candidates.json")}
        self.assertNotIn(("V001", "V076"), pairs)
        self.assertNotIn(("V151", "V152"), pairs)
        kinds = {r["kind"] for r in pairs[("V151", "V784")]["routes"]}
        self.assertTrue({"leaf_comembership", "density_comembership"} <= kinds)
        self.assertIn(("V152", "V785"), pairs)
        self.assertIn(("V001", "V151"), pairs)

    def test_top3_is_cross_note_distinct_note_with_deterministic_ties(self):
        audit = self.prepared()
        routes = [r for p in read(audit / "candidates.json") for r in p["routes"]
                  if r["kind"] == "cosine_top3" and r["source"] == "V151"]
        self.assertEqual(3, len(routes))
        self.assertEqual(3, len({self.instances[r["partner"]]["note_id"] for r in routes}))
        expected = []
        for note_id in sorted({i["note_id"] for i in self.instances.values()} - {self.instances["V151"]["note_id"]})[:3]:
            expected.append(min((i for i in self.instances.values() if i["note_id"] == note_id), key=lambda i: i["vector_id"])["instance"])
        self.assertEqual(expected, [r["partner"] for r in sorted(routes, key=lambda r: r["rank"])])
        self.assertTrue(all(r["cosine"] == 1.0 for r in routes))

    def test_same_note_noise_is_ineligible_but_cross_note_noise_is_eligible(self):
        instances = {v: dict(i) for v, i in self.instances.items()}
        excluded = {f"V{k:03d}" for k in range(151, 946)}
        self.assertTrue(_eligible(("V784", "V785"), instances, excluded))
        instances["V785"]["note_id"] = instances["V784"]["note_id"]
        self.assertFalse(_eligible(("V784", "V785"), instances, excluded))
        self.assertTrue(_eligible(("V001", "V784"), instances, excluded))
        self.assertFalse(_eligible(("V001", "V076"), instances, excluded))

    def test_sampling_is_disjoint_deterministic_and_blind_with_exact_instances(self):
        audit = self.prepared()
        proposals = self.out / "proposals.json"
        write(proposals, [["V945", "V944"], ["V944", "V945"]])
        for name in ("sample-a", "sample-b"):
            sample(audit, proposals, self.out / name)
        a, b = self.out / "sample-a", self.out / "sample-b"
        self.assertEqual((a / "review.json").read_bytes(), (b / "review.json").read_bytes())
        self.assertEqual((a / "sampling-manifest.json").read_bytes(), (b / "sampling-manifest.json").read_bytes())
        manifest = read(a / "sampling-manifest.json")
        self.assertEqual(20260908, manifest["seed"])
        sampled = manifest["selected"]
        self.assertEqual(128, len(sampled))
        self.assertEqual(128, len({p["pair_id"] for p in sampled}))
        pool = {tuple(p["pair"]): p for p in read(a / "pool.json")}
        self.assertIn("text_proposal", {r["kind"] for r in pool[("V944", "V945")]["routes"]})
        for stratum in ("proposed", "nonproposed"):
            rows = [p for p in sampled if p["stratum"] == stratum]
            self.assertEqual(64, len(rows))
            self.assertEqual(64, manifest["strata"][stratum]["n"])
            self.assertEqual(64 / manifest["strata"][stratum]["population"], manifest["strata"][stratum]["selection_probability"])
            for p in rows:
                self.assertEqual(stratum == "proposed", tuple(p["pair"]) in pool)
        review = read(a / "review.json")
        self.assertEqual(3, review["schema_version"])
        self.assertEqual(128, len(review["packets"]))
        self.assertNotEqual(sorted(p["packet"] for p in review["packets"]), [p["packet"] for p in review["packets"]])
        for p in review["packets"]:
            self.assertEqual({"packet", "question", "verdicts", "instances"}, set(p))
            self.assertEqual(REVIEW_QUESTION, p["question"])
            self.assertEqual(REVIEW_VERDICTS, p["verdicts"])
            self.assertEqual(2, len(p["instances"]))
            for i in p["instances"]:
                self.assertEqual(self.instances[i["instance"]], i)
            self.assertEqual("S" + hashlib.sha256(_canonical(sorted(i["vector_id"] for i in p["instances"]))).hexdigest()[:10], p["packet"])
        self.assertFalse({"routes", "cosine", "stratum", "scores", "labels", "methods", "judgments"} & set(review))
        catalog = read(audit / "mask-catalog.json")
        self.assertTrue(all(set(c) == {"id", "note_id", "fragments"} for c in catalog))
        self.assertEqual(["☕", "coffee"], catalog[0]["fragments"])

    def test_text_proposals_must_be_eligible_and_known(self):
        audit = self.prepared()
        for pair in (["V151", "V152"], ["V001", "V076"], ["V001", "V999"], ["V151", "V151"]):
            write(self.out / "bad.json", [pair])
            with self.assertRaises(ValueError):
                sample(audit, self.out / "bad.json", self.out / "bad-output")
            self.assertFalse((self.out / "bad-output").exists())

    def test_frozen_hash_mismatch_fails_before_output(self):
        source = self.root / "source/vectors"
        for name in ("vector-map.json", "normalized-vectors.f64le", "raw-vectors.f32le"):
            path = source / name
            raw = path.read_bytes()
            try:
                path.write_bytes(raw + b"x")
                with self.assertRaisesRegex(ValueError, "hash"):
                    prepare(self.root / "source", self.out / "bad")
                self.assertFalse((self.out / "bad").exists())
            finally:
                path.write_bytes(raw)

    def test_overwrite_refusal_and_audit_tampering(self):
        audit = self.prepared()
        with self.assertRaisesRegex(ValueError, "exists"):
            prepare(self.root / "source", audit)
        write(self.out / "proposals.json", [])
        sample(audit, self.out / "proposals.json", self.out / "sample")
        with self.assertRaisesRegex(ValueError, "exists"):
            sample(audit, self.out / "proposals.json", self.out / "sample")
        (audit / "excluded-ids.json").write_text("[]")
        with self.assertRaisesRegex(ValueError, "hash"):
            sample(audit, self.out / "proposals.json", self.out / "tampered")

    def test_actual_cli_prepare_and_sample(self):
        script = Path(__file__).with_name("omission_audit.py")
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        subprocess.run([sys.executable, str(script), "prepare", "--root", str(self.root / "source"),
                        "--output", str(self.out / "cli-audit")], check=True, env=env, capture_output=True)
        write(self.out / "proposals.json", [])
        subprocess.run([sys.executable, str(script), "sample", "--audit", str(self.out / "cli-audit"),
                        "--text-proposals", str(self.out / "proposals.json"), "--output", str(self.out / "cli-sample")],
                       check=True, env=env, capture_output=True)
        self.assertEqual(128, len(read(self.out / "cli-sample/review.json")["packets"]))

    def test_aliases_are_counted_without_deduplicating_vector_population(self):
        audit = self.prepared()
        manifest = read(audit / "manifest.json")
        aliases = manifest["source_mask_accounting"]
        self.assertEqual(167, aliases["distinct_total"])
        self.assertEqual(165, aliases["distinct_excluded"])
        self.assertEqual(778, aliases["vector_alias_count"])
        self.assertEqual(630, aliases["excluded_vector_alias_count"])
        self.assertEqual(0, aliases["excluded_aliases_of_covered_source_masks"])
        self.assertEqual(945, len(read(audit / "instances.json")))
        self.assertEqual(795, len(read(audit / "excluded-ids.json")))
        self.assertIn("not source-mask prevalence", manifest["unit"])
        ids = manifest["universe"]["index_order"]
        pairs = list(struct.iter_unpack("<II", (audit / "universe.u32le").read_bytes()))
        self.assertEqual(len(pairs), manifest["universe"]["pair_count"])
        self.assertEqual(sorted(set(pairs)), pairs)
        excluded = set(read(audit / "excluded-ids.json"))
        self.assertTrue(all(a < b and self.instances[ids[a]]["note_id"] != self.instances[ids[b]]["note_id"]
                            and (ids[a] in excluded or ids[b] in excluded) for a, b in pairs))

    def test_insufficient_stratum_is_an_error_not_a_smaller_sample(self):
        audit = self.prepared()
        # A deliberately tiny synthetic proposal stratum, with its new hash.
        write(audit / "candidates.json", [])
        manifest = read(audit / "manifest.json")
        manifest["files"]["candidates.json"] = identity(audit / "candidates.json")
        write(audit / "manifest.json", manifest)
        write(self.out / "proposals.json", [])
        with self.assertRaisesRegex(ValueError, "at least 64"):
            sample(audit, self.out / "proposals.json", self.out / "too-small")
        self.assertFalse((self.out / "too-small").exists())

    def test_review_manifest_declarations_are_checked_before_admission(self):
        for name in ("baseline", "leaf", "density"):
            path = self.root / f"source/hdbscan-{name}/review/manifest.json"
            original = path.read_bytes()
            for filename in ("review.json", "unassigned.json"):
                try:
                    document = json.loads(original)
                    document["files"][filename]["sha256"] = "0" * 64
                    write(path, document)
                    with self.assertRaisesRegex(ValueError, "hash"):
                        prepare(self.root / "source", self.out / "undeclared")
                    self.assertFalse((self.out / "undeclared").exists())
                finally:
                    path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
