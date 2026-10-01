"""Exercise reusable SP/MP collection through the supported experiment CLI."""
import json
import hashlib
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector.worker import _load_request


class HierarchyInputTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def masks(self, notes, adapter="masks"):
        self.write("mask-source.json", dict(schema_version=1, notes=notes))
        self.prompt.write_text("GENERIC PROMPT {POST}\n{INDEXED_POST}\n" +
                               ("{SUBJECTS}" if adapter == "grouped_masks" else "{SUBJECT}"))
        spec = json.loads(self.spec.read_text())
        spec["dataset"] = dict(adapter=adapter, path="mask-source.json")
        self.write("spec.json", spec)
        self.prepare("MP")

    def mask_response(self, selections):
        return dict(meaning="Tea", expressible=bool(selections), evidence="Source text.", mask=selections)

    def subjects(self, name="SP", notes=None, entries=None):
        notes = notes or [dict(note_id="a" * 64, text="é Tea Tea")]
        entries = entries if entries is not None else [
            dict(number="1", context="The post names tea.", subject="Drink"),
            dict(number="1.1", context="Tea is named twice.", subject="Tea")]
        self.write("posts.json", dict(schema_version=1, notes=notes))
        spec = json.loads(self.spec.read_text())
        spec["dataset"] = dict(adapter="subjects", path="posts.json")
        self.write("spec.json", spec)
        self.prepare(name)
        self.cli("run", name, env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(dict(subjects=entries))})
        return entries

    def test_collect_subjects_preserves_hierarchy_and_prepares_masks_offline(self):
        entries = self.subjects()
        calls = self.calls()
        self.cli("collect", "SP", "--output", "subjects")
        source = json.loads((self.root / "subjects/subjects.json").read_text())
        self.assertEqual(source["notes"][0]["subjects"], entries)
        self.assertEqual(source["notes"][0]["note_id"], "a" * 64)
        self.assertEqual(source["notes"][0]["text"], "é Tea Tea")
        self.assertIn("receipt", source["notes"][0]["origin"])
        self.prompt.write_text("GENERIC PROMPT {POST}\n{INDEXED_POST}\n{SUBJECT}")
        spec = json.loads(self.spec.read_text())
        spec["dataset"] = dict(adapter="masks", path="subjects/subjects.json")
        self.write("spec.json", spec)
        self.prepare("MP")
        cases = self.show("MP")["cases"]
        self.assertEqual([c["inputs"]["SUBJECT"] for c in cases], ["Drink", "Tea"])
        self.assertNotIn("Tea is named twice", cases[1]["prompt"])
        self.assertEqual(self.calls(), calls)

    def test_subject_preparation_accepts_200_complete_posts_without_calls(self):
        notes = [dict(note_id=f"{i:064x}", text=f"Original post {i}", area="food" if i < 100 else "music")
                 for i in range(200)]
        self.write("posts.json", dict(schema_version=1, notes=notes))
        spec = json.loads(self.spec.read_text())
        spec["dataset"] = dict(adapter="subjects", path="posts.json")
        self.write("spec.json", spec)
        self.prepare("SP")
        cases = self.show("SP")["cases"]
        self.assertEqual(len(cases), 200)
        self.assertEqual([c["inputs"]["POST"] for c in cases], [n["text"] for n in notes])
        self.assertTrue(all(set(c["inputs"]) == {"POST"} for c in cases))
        self.assertEqual(self.calls(), [])

    def test_collect_masks_preserves_empty_subjects_and_deduplicates_sse_inputs(self):
        entries = [dict(number=n, context="The source names tea.", subject=s)
                   for n, s in [("1", "Drink"), ("1.1", "Tea"), ("2", "Tea")]]
        self.subjects(entries=entries)
        self.cli("collect", "SP", "--output", "subjects")
        self.prompt.write_text("GENERIC PROMPT {POST}\n{INDEXED_POST}\n{SUBJECT}")
        spec = json.loads(self.spec.read_text())
        spec["dataset"] = dict(adapter="masks", path="subjects/subjects.json")
        self.write("spec.json", spec)
        self.prepare("MP")
        self.cli("run", "MP", "--max-new-attempts", "1", ok=False, env={
            "FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(dict(
                meaning="Drink", expressible=False, evidence="Only a specific drink is named.", mask=[]))})
        self.cli("run", "MP", env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(dict(
            meaning="Tea", expressible=True, evidence="The last tea mention.", mask=[[3, 3]]))})
        calls = self.calls()
        self.cli("collect", "MP", "--output", "sse")
        preserved = json.loads((self.root / "sse/masked-posts.json").read_text())["notes"][0]
        self.assertEqual([(s["number"], s["context"], s["subject"]) for s in preserved["subjects"]],
                         [(s["number"], s["context"], s["subject"]) for s in entries])
        self.assertEqual(preserved["subjects"][0]["byte_spans"], [])
        self.assertEqual(preserved["subjects"][1]["byte_spans"], [[7, 10]])
        mapping = json.loads((self.root / "sse/vector-map.json").read_text())
        self.assertEqual(len(mapping["vectors"]), 1)
        self.assertEqual(len(mapping["vectors"][0]["subject_entries"]), 2)
        proposal, notes = _load_request(self.root / "sse/worker-request.json")
        self.assertEqual(notes[0].text, "é Tea Tea")
        self.assertEqual(len(notes[0].subjects), 1)
        self.assertEqual(proposal, hashlib.sha256((self.root / "sse/masked-posts.json").read_bytes()).hexdigest())
        self.assertEqual(self.calls(), calls)

    def test_collect_multiple_subject_batches_reuses_saved_answers_and_keeps_metadata(self):
        notes = [dict(note_id="a" * 64, text="Tea", pubkey="public-author-a"),
                 dict(note_id="b" * 64, text="Coffee", pubkey="public-author-b")]
        self.subjects(notes=notes)
        calls = self.calls()
        for name, note in zip(["first", "second"], notes):
            self.cli("prepare", name, "--from", "SP", "--only", note["note_id"])
            self.cli("run", name)
        self.cli("collect", "first", "second", "--output", "combined")
        result = json.loads((self.root / "combined/subjects.json").read_text())["notes"]
        self.assertEqual([n["note_id"] for n in result], [n["note_id"] for n in notes])
        self.assertEqual([n["pubkey"] for n in result], [n["pubkey"] for n in notes])
        self.assertTrue(all(n["origin"]["reused"] for n in result))
        self.assertEqual(self.calls(), calls)
        error = self.cli("collect", "first", "first", "--output", "duplicate", ok=False)
        self.assertIn("duplicate collected post", error.stderr)
        self.assertFalse((self.root / "duplicate").exists())

    def test_collected_subjects_can_be_prepared_again_with_their_post_identities(self):
        notes = [dict(note_id="a" * 64, text="Tea", origin=dict(prompt_id="N001")),
                 dict(note_id="b" * 64, text="Coffee", origin=dict(prompt_id="N002"))]
        self.subjects(notes=notes)
        self.cli("collect", "SP", "--output", "collected")
        spec = json.loads(self.spec.read_text())
        spec["dataset"]["path"] = "collected/subjects.json"
        self.write("spec.json", spec)
        calls = self.calls()
        self.prepare("again")
        self.assertEqual([c["id"] for c in self.show("again")["cases"]], ["N001", "N002"])
        self.assertEqual(self.calls(), calls)

    def test_subject_numbering_is_validated_without_repairs_or_retries(self):
        self.subjects()
        self.cli("prepare", "bad", "--from", "SP", "--repeat")
        bad = dict(subjects=[dict(number="1.1", context="Tea in the post.", subject="Tea")])
        self.cli("run", "bad", ok=False, env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(bad)})
        report = self.show("bad")
        self.assertEqual(report["summary"]["attempts"], 1)
        self.assertEqual(report["summary"]["malformed"], 1)
        self.assertIn("invalid subject numbering", report["cases"][0]["error"])
        self.cli("collect", "bad", "--output", "invalid", ok=False)
        self.assertFalse((self.root / "invalid").exists())

    def test_collection_rejects_unrun_changed_sources_and_tampered_receipts(self):
        self.subjects()
        calls = self.calls()
        self.cli("prepare", "unrun", "--from", "SP")
        self.cli("collect", "unrun", "--output", "missing", ok=False)
        self.assertFalse((self.root / "missing").exists())
        source = self.root / "posts.json"
        original = source.read_bytes()
        source.write_bytes(original + b"\n")
        error = self.cli("collect", "SP", "--output", "changed", ok=False)
        self.assertIn("protected source changed", error.stderr)
        self.assertFalse((self.root / "changed").exists())
        source.write_bytes(original)
        ledger = self.root / "SP/run/results.jsonl"
        records = [json.loads(line) for line in ledger.read_text().splitlines()]
        records[0]["final_output_raw"] = '{"subjects":[]}'
        ledger.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        self.cli("collect", "SP", "--output", "tampered", ok=False)
        self.assertFalse((self.root / "tampered").exists())
        self.assertEqual(self.calls(), calls)

    def test_collection_refuses_overwrites_and_outputs_inside_experiments(self):
        self.subjects()
        self.cli("collect", "SP", "--output", "collected")
        path = self.root / "collected/subjects.json"
        original = path.read_bytes()
        self.cli("collect", "SP", "--output", "collected", ok=False)
        self.assertEqual(path.read_bytes(), original)
        self.cli("collect", "SP", "--output", "SP/collected", ok=False)
        self.assertFalse((self.root / "SP/collected").exists())

    def test_collection_combines_partial_mask_batches_only_when_complete(self):
        self.masks([dict(note_id="a" * 64, text="Tea Tea", subjects=[
            dict(number=n, context="Tea in the post.", subject=s)
            for n, s in [("1", "Drink"), ("1.1", "Tea")]])])
        cases = self.show("MP")["cases"]
        for name, case in zip(["first", "second"], cases):
            self.cli("prepare", name, "--from", "MP", "--only", case["id"])
            self.cli("run", name, env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(self.mask_response([[2, 2]]))})
        error = self.cli("collect", "first", "--output", "partial", ok=False)
        self.assertIn("missing subject mask", error.stderr)
        self.assertFalse((self.root / "partial").exists())
        self.cli("collect", "first", "second", "--output", "complete")
        mapping = json.loads((self.root / "complete/vector-map.json").read_text())
        self.assertEqual(len(mapping["vectors"]), 1)
        self.assertEqual(len(mapping["vectors"][0]["subject_entries"]), 2)

    def test_grouped_mask_collection_preserves_each_sp_entry(self):
        entries = [dict(number=n, context="Tea in the post.", subject="Tea") for n in ["1", "1.1"]]
        self.masks([dict(note_id="a" * 64, text="Tea Tea", subjects=entries)], "grouped_masks")
        response = dict(results=[dict(id=f"S{i}", **self.mask_response([[2, 2]])) for i in [1, 2]])
        self.cli("run", "MP", env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(response)})
        calls = self.calls()
        self.cli("collect", "MP", "--output", "sse")
        mapping = json.loads((self.root / "sse/vector-map.json").read_text())
        self.assertEqual([s["number"] for s in mapping["vectors"][0]["subject_entries"]], ["1", "1.1"])
        self.assertEqual(self.calls(), calls)

    def test_empty_masks_and_posts_without_subjects_need_no_sse_request(self):
        self.masks([dict(note_id="a" * 64, text="Tea", subjects=[dict(
            number="1", context="A drink is implied.", subject="Drink")]),
            dict(note_id="b" * 64, text="https://example.com", subjects=[])])
        self.cli("run", "MP", env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(self.mask_response([]))})
        self.cli("collect", "MP", "--output", "empty")
        preserved = json.loads((self.root / "empty/masked-posts.json").read_text())["notes"]
        self.assertEqual(len(preserved), 2)
        self.assertEqual(preserved[0]["subjects"][0]["byte_spans"], [])
        self.assertEqual(preserved[1]["subjects"], [])
        self.assertFalse((self.root / "empty/worker-request.json").exists())

    def test_subject_vector_preparation_retains_a_post_with_only_empty_masks(self):
        from sse_multivector.subject_order_probe import build_inputs
        posts = dict(notes=[dict(note_id=nid, text="Tea", subjects=[dict(
            number="1", subject="Tea", context="Tea in the post.",
            byte_spans=spans, fragments=fragments)]) for nid, spans, fragments in [
                ("a" * 64, [[0, 3]], ["Tea"]), ("b" * 64, [], [])]])
        mapping = dict(notes=[dict(note_id="a" * 64, short_id="N001"),
                              dict(note_id="b" * 64, short_id="N002")],
                       vectors=[dict(note_id="a" * 64, note_short_id="N001",
                                     vector_id="v", byte_spans=[[0, 3]])])
        inputs, request = build_inputs(posts, mapping, ["N001", "N002"])
        self.assertEqual(len(inputs["posts"]), 2)
        self.assertEqual(len(inputs["subjects"]), 2)
        self.assertEqual(inputs["subjects"][1]["mask_vector_ids"], [])
        self.assertEqual(len(request["notes"]), 1)

    def test_collection_binds_supplied_sse_settings_without_running_worker(self):
        self.masks([dict(note_id="a" * 64, text="Tea", subjects=[dict(
            number="1", context="Tea in the post.", subject="Tea")])])
        self.cli("run", "MP", env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(self.mask_response([[1, 1]]))})
        config = dict(schema_version=1, request_path="old-request", request_sha256="1" * 64,
                      checkpoint_path="/models/checkpoint", checkpoint_sha256="2" * 64,
                      base_model_artifact_path="/models/base", base_model_artifact_tree_sha256="3" * 64,
                      model=dict(base_model="sentence-transformers/sentence-t5-base", dimensions=768,
                                 maximum_tokens=512, pooling="selected-contextual-token-mean-linear-relu-linear-v1"),
                      device="cpu", container_image="sha256:" + "4" * 64, note_batch_size=8,
                      output_path="old-output")
        path = self.write("worker-settings.json", config)
        calls = self.calls()
        self.cli("collect", "MP", "--output", "sse", "--worker-config", path)
        from sse_multivector.worker import WorkerConfig
        bound = WorkerConfig.load(self.root / "sse/worker-config.json")
        self.assertEqual(bound.request_path, self.root / "sse/worker-request.json")
        self.assertEqual(bound.request_sha256, hashlib.sha256(bound.request_path.read_bytes()).hexdigest())
        self.assertEqual(bound.output_path, self.root / "sse/worker-result")
        self.assertEqual(bound.checkpoint_sha256, config["checkpoint_sha256"])
        self.assertEqual(bound.model.to_json(), config["model"])
        self.assertEqual(bound.note_batch_size, config["note_batch_size"])
        self.assertEqual(json.loads(path.read_text()), config)
        self.assertFalse(bound.output_path.exists())
        self.assertEqual(self.calls(), calls)


if __name__ == "__main__":
    unittest.main()
