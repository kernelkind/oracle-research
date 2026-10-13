"""V3 construction through the shared CLI and ordinary native receipts."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from sse_multivector import test_experiment as fixtures
from sse_multivector.worker import canonical_tree_sha256
from sse_multivector import worker


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"


class FixtureEncoder:
    def encode(self, notes):
        for note in notes:
            for subject in note.subjects:
                yield worker.EncodedSubject(
                    note_id=note.note_id,
                    subject_id=subject.subject_id,
                    vector=(1.0, 1.0, 1.0),
                    selected_token_indices=(1,),
                    selected_token_ids=(101,),
                    token_count=3,
                )


class HierarchyGenerationV3Tests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    calls = fixtures.ExperimentTests.calls

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run(
            [str(LAUNCHER), "--project-root", str(PROJECT), *map(str, args)],
            cwd=self.root,
            env={**os.environ, "FAKE_RUNNER_LOG": str(self.log), **(env or {})},
            text=True,
            capture_output=True,
            timeout=120,
        )
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def configure(self, count=10, notes=None):
        self.prompt.write_text("GENERIC PROMPT {INPUT_JSON}")
        notes = notes or [
            dict(
                note_id=f"n{i}",
                text=f"Original post {i}",
                origin=dict(prompt_version="ASv6.100"),
                subjects=[
                    dict(number="1", subject=f"Topic {i}", context="Original role"),
                    dict(
                        number="1.1", subject="Unused local child", context="Child role"
                    ),
                ],
            )
            for i in range(count)
        ]
        self.write("notes.json", dict(schema_version=1, notes=notes))
        base = json.loads(self.spec.read_text())
        for name, schema in (
            (
                "bootstrap",
                {
                    "type": "object",
                    "properties": {"meaning": {"type": ["string", "null"]}},
                    "required": ["meaning"],
                    "additionalProperties": False,
                },
            ),
            (
                "consolidation",
                {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "meaning": {"type": "string"},
                    },
                    "required": ["title", "meaning"],
                    "additionalProperties": False,
                },
            ),
        ):
            self.write(
                name + ".json",
                {**base, "runner": {**base["runner"], "output_schema": schema}},
            )
        checkpoint = self.root / "checkpoint.ckpt"
        checkpoint.write_bytes(b"Offline encoder fixture")
        artifact = self.root / "encoder-model"
        artifact.mkdir()
        (artifact / "tokenizer.json").write_text("{}")
        self.write(
            "worker.json",
            dict(
                schema_version=1,
                request_path="unused",
                request_sha256="ab" * 32,
                checkpoint_path=str(checkpoint),
                checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                base_model_artifact_path=str(artifact),
                base_model_artifact_tree_sha256=canonical_tree_sha256(artifact),
                model=dict(
                    base_model="fixture/encoder",
                    dimensions=3,
                    maximum_tokens=512,
                    pooling="selected-contextual-token-mean-linear-relu-linear-v1",
                ),
                device="cpu",
                container_image="sha256:" + "ef" * 32,
                note_batch_size=16,
                output_path="unused",
            ),
        )
        return self.write(
            "hierarchy.json",
            dict(
                schema_version=1,
                corpus="notes.json",
                note_ids=[n["note_id"] for n in notes],
                local_schema_version=4,
                bootstrap_spec="bootstrap.json",
                consolidation_spec="consolidation.json",
                worker_config="worker.json",
            ),
        )

    def automatic_runner(self):
        text = self.runner.read_text()
        needle = 'if stage == "prompt":\n'
        self.assertIn(needle, text)
        code = """if stage == "prompt" and os.environ.get("FAKE_V3"):
    import hashlib
    payload=json.loads(prompt.removeprefix("GENERIC PROMPT "))
    if "local" in payload:
        local=payload["local"]
        subject=next(e["subject"] for e in local["hierarchy"]["entries"]
                     if e["number"]==local["hierarchy"]["selected"])
        value={"meaning":"Definition of "+subject}
    else:
        title="Group "+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:12]
        value={"title":title,"meaning":"Definition of "+title}
    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"]=json.dumps(value)
"""
        self.runner.write_text(text.replace(needle, code + "\n" + needle))

    def state(self):
        return json.loads((self.root / "trial/state.json").read_text())

    def bootstrap(self, meaning="Established meaning"):
        experiment = self.state()["experiments"][0]["experiment"]
        self.cli(
            "run",
            experiment,
            env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(dict(meaning=meaning))},
        )
        self.cli("advance-hierarchy", "trial", "--comment", "Collect native Bootstrap")

    def encode_pending(self):
        for row in self.state()["encodings"]:
            if not row.get("complete"):
                with patch(
                    "sse_multivector.worker.OfficialSseEncoder",
                    return_value=FixtureEncoder(),
                ):
                    worker.run_worker(row["config"])
        self.cli(
            "advance-hierarchy",
            "trial",
            "--comment",
            "Collect ordinary worker receipts",
        )

    def test_prepare_selects_every_original_l1_and_only_bootstrap_without_inference(
        self,
    ):
        spec = self.configure(count=10)
        self.cli("prepare-hierarchy", "trial", "--spec", spec)
        state = self.state()
        self.assertEqual(state["generation_policy"], "hierarchy-generation-v3")
        self.assertEqual(len(state["originals"]), 10)
        self.assertTrue(
            all(row["local"]["number"] == "1" for row in state["originals"])
        )
        self.assertEqual([row["role"] for row in state["experiments"]], ["bootstrap"])
        self.assertEqual(len(state["experiments"][0]["inputs"]), 10)
        self.assertEqual(state["nodes"], [])
        self.assertEqual(self.calls(), [])

    def test_ten_original_vectors_produce_all_five_pairs_and_five_canonical_roots(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure())
        self.bootstrap()
        request = json.loads(
            (
                Path(self.state()["encodings"][0]["config"]).parent / "request.json"
            ).read_text()
        )
        self.assertEqual(len(request["notes"]), 10)
        for note in request["notes"]:
            subject = note["text"].split("\n\n")[0]
            self.assertEqual(
                note["subjects"][0]["byte_spans"], [[0, len(subject.encode())]]
            )
            self.assertEqual(note["text"], subject + "\n\nEstablished meaning")
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["families"][0]["rounds"][0]["comparisons"], 45)
        self.assertEqual(len(state["families"][0]["rounds"][0]["pairs"]), 5)
        experiment = state["experiments"][1]["experiment"]
        payloads = [
            json.loads(value["INPUT_JSON"])
            for value in state["experiments"][1]["inputs"].values()
        ]
        self.assertTrue(
            all(
                set(value) == {"nodes"} and len(value["nodes"]) == 2
                for value in payloads
            )
        )
        self.cli(
            "run",
            experiment,
            env={
                "FAKE_RUNNER_PROMPT_RESPONSE": '{"title":"Combined topic","meaning":"Combined meaning"}'
            },
        )
        self.cli("advance-hierarchy", "trial", "--comment", "Promote final five")
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["nodes"]), 5)
        self.assertEqual([len(n["original_ids"]) for n in state["nodes"]], [2] * 5)
        self.assertEqual(
            {i for n in state["nodes"] for i in n["original_ids"]},
            {row["id"] for row in state["originals"]},
        )
        self.assertTrue(all(not node["parents"] for node in state["nodes"]))
        self.assertEqual(len(self.calls()), 15)
        before = (self.root / "trial/state.json").read_bytes()
        self.cli(
            "advance-hierarchy", "trial", "--comment", "Idempotent completed resume"
        )
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)

    def test_null_bootstrap_keeps_all_entries_and_prevents_root_construction(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=3))
        self.bootstrap(meaning=None)
        state = self.state()
        self.assertEqual(state["status"], "blocked_bootstrap")
        self.assertEqual(len(state["originals"]), 3)
        self.assertEqual(len(state["unresolved"]), 3)
        self.assertEqual(state["encodings"], [])
        self.assertEqual(state["nodes"], [])

    def test_automatic_recursion_restarts_original_l1s_and_supplies_canonical_parent(
        self,
    ):
        from sse_multivector import hierarchy_generation as generation

        self.configure(count=28)
        self.automatic_runner()
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            result = generation.run(self.root / "trial", None)
        self.assertEqual(result["status"], "complete")
        state = self.state()
        roots = [n for n in state["nodes"] if not n["parents"]]
        self.assertEqual(len(roots), 4)
        by_id = {n["id"]: n for n in state["nodes"]}
        self.assertTrue(any(n["parents"] for n in state["nodes"]))
        for family in state["families"]:
            self.assertTrue(family["complete"])
            self.assertTrue(all(i.startswith("L") for i in family["original_ids"]))
            if family["parent"] is not None:
                parent = by_id[family["parent"]]
                self.assertEqual(family["original_ids"], parent["original_ids"])
                self.assertTrue(
                    all(i.startswith("L") for i in family["rounds"][0]["current"])
                    if family["rounds"]
                    else True
                )
                for round_ in family["rounds"]:
                    inputs = state["experiments"][round_["experiment"]]["inputs"]
                    for case in inputs.values():
                        self.assertEqual(
                            json.loads(case["INPUT_JSON"])["parent"],
                            dict(title=parent["subject"], meaning=parent["meaning"]),
                        )
        children = {n["id"]: [] for n in state["nodes"]}
        for node in state["nodes"]:
            for parent in node["parents"]:
                children[parent].append(node)
        for node in state["nodes"]:
            self.assertLessEqual(len(children[node["id"]]), 6)
            if not children[node["id"]]:
                self.assertLessEqual(len({e["note_id"] for e in node["entries"]}), 2)
            else:
                self.assertEqual(
                    {
                        i
                        for child in children[node["id"]]
                        for i in child["original_ids"]
                    },
                    set(node["original_ids"]),
                )
        count = len(self.calls())
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ) as encoder,
        ):
            self.assertEqual(
                generation.run(self.root / "trial", None)["status"], "complete"
            )
            encoder.assert_not_called()
        self.assertEqual(len(self.calls()), count)

    def test_odd_family_carries_unpaired_original_without_reencoding_or_losing_it(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=7))
        self.bootstrap()
        self.encode_pending()
        state = self.state()
        round_ = state["families"][0]["rounds"][0]
        self.assertEqual(round_["comparisons"], 21)
        self.assertEqual(len(round_["pairs"]), 3)
        self.assertEqual(round_["unpaired"], ["L00007"])
        self.cli(
            "run",
            state["experiments"][1]["experiment"],
            env={
                "FAKE_RUNNER_PROMPT_RESPONSE": '{"title":"Combined","meaning":"Combined meaning"}'
            },
        )
        self.cli("advance-hierarchy", "trial", "--comment", "Collect odd family")
        request = json.loads(
            (
                Path(self.state()["encodings"][1]["config"]).parent / "request.json"
            ).read_text()
        )
        self.assertEqual(
            [n["text"] for n in request["notes"]], ["Combined\n\nCombined meaning"]
        )
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["nodes"]), 4)
        carried = next(n for n in state["nodes"] if n["original_ids"] == ["L00007"])
        self.assertEqual(carried["subject"], "Topic 6")
        self.assertIn("bootstrap", carried)

    def test_distinct_notes_not_entry_count_controls_expansion(self):
        from sse_multivector import hierarchy_generation as generation

        notes = [
            dict(
                note_id=f"n{n}",
                text=f"Post {n}",
                origin=dict(prompt_version="ASv6.100"),
                subjects=[
                    dict(number=str(i + 1), subject=f"Topic {n}-{i}", context="Role")
                    for i in range(4)
                ],
            )
            for n in range(7)
        ]
        self.configure(notes=notes)
        self.automatic_runner()
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            generation.run(self.root / "trial")
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["nodes"]), 4)
        self.assertEqual(len(state["families"]), 1)
        self.assertTrue(any(len(n["original_ids"]) > 2 for n in state["nodes"]))
        self.assertTrue(
            all(len({e["note_id"] for e in n["entries"]}) <= 2 for n in state["nodes"])
        )

    def test_completed_trial_reuses_exact_native_answers_in_new_trial(self):
        from sse_multivector import hierarchy_generation as generation

        self.configure()
        self.automatic_runner()
        for directory in ("trial", "reuse"):
            self.cli(
                "prepare-hierarchy", directory, "--spec", self.root / "hierarchy.json"
            )
            with (
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
                patch(
                    "sse_multivector.worker.OfficialSseEncoder",
                    return_value=FixtureEncoder(),
                ),
            ):
                result = generation.run(self.root / directory)
            self.assertEqual(result["status"], "complete")
            if directory == "trial":
                calls = len(self.calls())
        self.assertEqual(len(self.calls()), calls)
        state = json.loads((self.root / "reuse/state.json").read_text())
        for record in state["experiments"]:
            shown = json.loads(self.cli("show", record["experiment"], "--json").stdout)
            self.assertTrue(all(case["reused"] for case in shown["cases"]))

    def test_partial_run_resumes_without_repeating_successful_calls(self):
        from sse_multivector import hierarchy_generation as generation

        self.configure()
        self.automatic_runner()
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        budget = self.write("allowance.json", dict(schema_version=1, limit=10, used=0))
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            self.assertEqual(
                generation.run(self.root / "trial", budget)["execution_status"],
                "blocked",
            )
            self.assertEqual(len(self.calls()), 10)
            producer = (
                Path(self.state()["experiments"][0]["experiment"]) / "run/results.jsonl"
            )
            receipt = producer.read_bytes()
            settings = json.loads(budget.read_text())
            settings["limit"] = 20
            budget.write_text(json.dumps(settings))
            self.assertEqual(
                generation.run(self.root / "trial", budget)["status"], "complete"
            )
        self.assertEqual(producer.read_bytes(), receipt)
        self.assertEqual(len(self.calls()), 15)

    def runner_outage_fixture(self, *, count=7, after_calls=7, remaining=2):
        self.configure(count=count)
        self.automatic_runner()
        needle = 'if "--version" in sys.argv:\n'
        code = """if os.environ.get("FAKE_RUNNER_OUTAGE") and ("--version" in sys.argv or "--identity" in sys.argv):
    outage=Path(os.environ["FAKE_RUNNER_OUTAGE"])
    settings=json.loads(outage.read_text())
    log=Path(os.environ["FAKE_RUNNER_LOG"])
    calls=json.loads(log.read_text()) if log.exists() else []
    if len(calls)>=settings["after_calls"] and settings["remaining"]:
        settings["remaining"]-=1
        settings["parents"].append(os.getppid())
        outage.write_text(json.dumps(settings))
        raise SystemExit("temporary experiment runner outage")
"""
        self.runner.write_text(self.runner.read_text().replace(needle, code + needle))
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        return self.write(
            "outage.json",
            dict(remaining=remaining, after_calls=after_calls, parents=[]),
        )

    def test_runner_outage_backs_off_and_restarts_without_repeating_saved_calls(self):
        from sse_multivector import hierarchy_generation as generation

        outage = self.runner_outage_fixture()
        with (
            patch.dict(
                os.environ,
                FAKE_RUNNER_LOG=str(self.log),
                FAKE_V3="1",
                FAKE_RUNNER_OUTAGE=str(outage),
            ),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
            patch.object(generation, "RUNNER_BACKOFF_SECONDS", 0.001, create=True),
        ):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(self.calls()), 10)
        failure = json.loads(outage.read_text())
        self.assertEqual(failure["remaining"], 0)
        self.assertEqual(len(set(failure["parents"])), 2)
        events = [
            json.loads(line)
            for line in (self.root / "trial/runner-backoff.jsonl")
            .read_text()
            .splitlines()
        ]
        self.assertEqual(
            [r["delay_seconds"] for r in events if r["event"] == "backoff"],
            [0.001, 0.002],
        )
        self.assertEqual(events[-1]["event"], "recovered")

    def test_runner_execution_outage_has_capped_backoff_and_no_model_resampling(self):
        from sse_multivector import hierarchy_generation as generation

        outage = self.runner_outage_fixture(after_calls=0, remaining=4)
        with (
            patch.dict(
                os.environ,
                FAKE_RUNNER_LOG=str(self.log),
                FAKE_V3="1",
                FAKE_RUNNER_OUTAGE=str(outage),
            ),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
            patch.object(generation, "RUNNER_BACKOFF_SECONDS", 0.001),
            patch.object(generation, "RUNNER_BACKOFF_MAX_SECONDS", 0.002),
        ):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(self.calls()), 10)
        events = [
            json.loads(line)
            for line in (self.root / "trial/runner-backoff.jsonl")
            .read_text()
            .splitlines()
        ]
        retries = [row for row in events if row["event"] == "backoff"]
        self.assertEqual(
            [r["delay_seconds"] for r in retries], [0.001, 0.002, 0.002, 0.002]
        )
        self.assertEqual({r["command"] for r in retries}, {"run"})
        self.assertEqual(len(set(json.loads(outage.read_text())["parents"])), 4)

    def test_runner_backoff_can_be_interrupted_without_dispatching_a_model_call(self):
        from threading import Event
        from sse_multivector import hierarchy_generation as generation

        outage = self.runner_outage_fixture(count=3, after_calls=0, remaining=100)
        stop = Event()

        def interrupt(delay):
            stop.set()
            return True

        with (
            patch.dict(
                os.environ,
                FAKE_RUNNER_LOG=str(self.log),
                FAKE_V3="1",
                FAKE_RUNNER_OUTAGE=str(outage),
            ),
            patch.object(stop, "wait", side_effect=interrupt) as wait,
        ):
            self.assertIsNone(
                generation._native_teacher(
                    self.root / "trial",
                    Path(self.state()["experiments"][0]["experiment"]),
                    None,
                    None,
                    stop,
                )
            )
        wait.assert_called_once_with(5)
        self.assertEqual(len(self.calls()), 0)
        self.assertEqual(json.loads(outage.read_text())["remaining"], 99)

    def test_malformed_model_answers_block_instead_of_entering_runner_backoff(self):
        from sse_multivector import hierarchy_generation as generation

        self.configure(count=7)
        self.automatic_runner()
        script = self.runner.read_text()
        needle = 'value={"title":title,"meaning":"Definition of "+title}'
        self.assertIn(needle, script)
        self.runner.write_text(script.replace(needle, "value=None"))
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["execution_status"], "blocked")
        self.assertEqual(len(self.calls()), 10)
        events = [
            json.loads(line)
            for line in (self.root / "trial/runner-backoff.jsonl")
            .read_text()
            .splitlines()
        ]
        self.assertEqual([row["event"] for row in events], ["blocked"])

    def test_invalid_pair_output_is_reported_and_does_not_drop_originals(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure())
        self.bootstrap()
        self.encode_pending()
        state = self.state()
        self.cli(
            "run",
            state["experiments"][1]["experiment"],
            ok=False,
            env={"FAKE_RUNNER_PROMPT_RESPONSE": "null"},
        )
        result = json.loads(
            self.cli(
                "advance-hierarchy", "trial", "--comment", "Collect invalid proposal"
            ).stdout
        )
        self.assertEqual(len(result["unresolved"]), 5)
        self.assertTrue(all(c["status"] == "malformed" for c in result["unresolved"]))
        state = self.state()
        self.assertEqual(state["nodes"], [])
        self.assertEqual(
            set(state["families"][0]["current"]),
            {row["id"] for row in state["originals"]},
        )

    def test_tampered_native_or_vector_receipt_cannot_change_completed_graph(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=3))
        self.bootstrap()
        self.encode_pending()
        before = (self.root / "trial/state.json").read_bytes()
        producer = (
            Path(self.state()["experiments"][0]["experiment"]) / "run/results.jsonl"
        )
        raw = producer.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        rows[0]["final_output_raw"] = '{"meaning":"Tampered"}'
        producer.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.cli(
            "advance-hierarchy",
            "trial",
            "--comment",
            "Reject changed receipt",
            ok=False,
        )
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)
        producer.write_bytes(raw)
        path = (
            Path(self.state()["encodings"][0]["config"]).parent
            / "worker-result/raw-vectors.f32le"
        )
        path.write_bytes(b"\0" * len(path.read_bytes()))
        self.cli(
            "advance-hierarchy",
            "trial",
            "--comment",
            "Reject changed vectors",
            ok=False,
        )
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)

    def test_exact_pair_ranking_and_spill_merge_choose_global_highest_unique_pairs(
        self,
    ):
        from sse_multivector import hierarchy_generation as generation

        vectors = [(1.0, 0.0), (0.0, 1.0), (0.0, 2.0), (2.0, 0.0), (-1.0, 0.0)]
        pairs = generation._rank_pairs(vectors, self.root)
        self.assertEqual([(a, b) for a, b, score in pairs], [(0, 3), (1, 2)])
        self.assertEqual([score for a, b, score in pairs], [1.0, 1.0])
        with (
            patch.object(generation, "PAIR_CHUNK_ROWS", 1),
            patch.object(generation, "PAIR_MERGE_FANIN", 2),
        ):
            self.assertEqual(generation._rank_pairs(vectors, self.root), pairs)
        self.assertFalse(list(self.root.glob(".cosine-pairs-*")))

    def test_shared_cli_exposes_v3_and_retires_v2_constructor(self):
        help_text = self.cli("--help").stdout
        for command in ("prepare-hierarchy", "advance-hierarchy", "run-hierarchy"):
            self.assertIn(command, help_text)
        self.assertNotIn("canonical-traversal", help_text)
        run_help = self.cli("run-hierarchy", "--help").stdout
        self.assertIn("--attempt-budget", run_help)
        self.assertNotIn("--concurrency", run_help)

    def test_bad_worker_configuration_is_rejected_before_bootstrap_preparation(self):
        spec = self.configure(count=3)
        config = json.loads((self.root / "worker.json").read_text())
        config["model"]["dimensions"] = 0
        self.write("worker.json", config)
        self.cli("prepare-hierarchy", "trial", "--spec", spec, ok=False)
        self.assertFalse((self.root / "trial").exists())
        self.assertEqual(self.calls(), [])

    def test_pair_adapter_rejects_nonpairs_before_inference(self):
        self.prompt.write_text("GENERIC PROMPT {INPUT_JSON}")
        spec = json.loads(self.spec.read_text())
        spec["dataset"] = dict(
            adapter="hierarchy_pair_consolidation", path="pair-source.json"
        )
        self.write(
            "pair-source.json",
            dict(
                cases=[
                    dict(id="bad", inputs={"INPUT_JSON": json.dumps(dict(nodes=[]))})
                ]
            ),
        )
        self.write("pair-spec.json", spec)
        self.cli("prepare", "invalid-pair", "--spec", "pair-spec.json", ok=False)
        self.assertFalse((self.root / "invalid-pair").exists())
        self.assertEqual(self.calls(), [])

    def test_pair_prompt_family_requires_its_pinned_assembly(self):
        self.prompt.write_text("GENERIC PROMPT {POST}")
        spec = json.loads(self.spec.read_text())
        spec["prompt"]["id"] = "Hierarchy-pair-consolidation-v2"
        self.write("pair-spec.json", spec)
        result = self.cli(
            "prepare", "unbound-prompt", "--spec", "pair-spec.json", ok=False
        )
        self.assertIn("paired assembly", result.stderr)
        self.assertFalse((self.root / "unbound-prompt").exists())

    def test_saved_control_parameters_cannot_change_frozen_definition(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=3))
        state = self.state()
        state["consolidation_spec"]["runner"]["model"] = "Unapproved switched model"
        self.write("trial/state.json", state)
        original = (self.root / "trial/state.json").read_bytes()
        self.cli(
            "advance-hierarchy", "trial", "--comment", "Reject changed model", ok=False
        )
        self.assertEqual((self.root / "trial/state.json").read_bytes(), original)
        self.assertEqual(self.calls(), [])

    def test_existing_viewer_and_compare_preparation_accept_completed_v3_nodes(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=3))
        self.bootstrap()
        self.encode_pending()
        before = (self.root / "trial/state.json").read_bytes()
        self.cli("export-canonical-viewer", "trial", "--output", "view")
        view = json.loads((self.root / "view/hierarchy.json").read_text())
        self.assertEqual(len(view["notes"]), 3)
        node = self.state()["nodes"][0]
        self.write(
            "compare-source.json",
            dict(
                schema_version=2,
                corpus="notes.json",
                canonical_states=dict(current=dict(trial="trial/state.json")),
                pairs=[
                    dict(
                        id="one",
                        local=dict(note_id="n1", number="1"),
                        canonical=dict(state="current", id=node["id"]),
                        review={},
                    )
                ],
            ),
        )
        spec = json.loads((self.root / "bootstrap.json").read_text())
        spec["dataset"] = dict(
            adapter="hierarchy_node_pairs", path="compare-source.json"
        )
        spec["runner"]["output_schema"] = json.loads(
            (
                PROJECT
                / "sse_multivector/shr_single_pair/Hierarchy-compare-v4.output.schema.json"
            ).read_text()
        )
        self.write("compare-spec.json", spec)
        self.cli("prepare", "inspect", "--spec", "compare-spec.json")
        shown = json.loads(
            self.cli("show", "inspect", "--case", "one", "--json").stdout
        )
        self.assertEqual(
            json.loads(shown["inputs"]["INPUT_JSON"])["canonical"]["meaning"],
            node["meaning"],
        )
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)
        self.assertEqual(len(self.calls()), 3)


if __name__ == "__main__":
    unittest.main()
