"""V3 construction through the shared CLI and ordinary native receipts."""

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tracemalloc
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


class CutoffFixtureEncoder:
    """Controlled vectors supplied through the ordinary SSE worker interface."""

    def __init__(self, dimensions, scores=(0.8, 0.7, 0.6, 0.2)):
        self.dimensions = dimensions
        self.scores = scores

    def encode(self, notes):
        for note in notes:
            index = int(note.text.split("\n\n")[0].split()[-1])
            vector = [0.0] * self.dimensions
            if index % 2 and index < 8:
                score = self.scores[index // 2]
                vector[index - 1] = score
                vector[index] = math.sqrt(1 - score * score)
            else:
                vector[index] = 1.0
            for subject in note.subjects:
                yield worker.EncodedSubject(
                    note_id=note.note_id,
                    subject_id=subject.subject_id,
                    vector=tuple(vector),
                    selected_token_indices=(1,),
                    selected_token_ids=(101,),
                    token_count=3,
                )


class HierarchyGenerationV3Tests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    calls = fixtures.ExperimentTests.calls

    def test_reading_one_vector_does_not_expand_all_binary_rows_into_python_floats(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.configure(count=32)
        self.automatic_runner()
        config = json.loads((self.root/'worker.json').read_text())
        dimensions = 32768
        config['model']['dimensions'] = dimensions
        self.write('worker.json', config)
        self.cli('prepare-hierarchy', 'trial', '--spec', spec)
        self.cli('run', self.state()['experiments'][0]['experiment'], env={'FAKE_V3': '1'})
        self.cli('advance-hierarchy', 'trial', '--comment', 'Collect fixture meanings')
        state = self.state()

        class WideEncoder:
            def encode(self, notes):
                for note in notes:
                    for subject in note.subjects:
                        yield worker.EncodedSubject(note_id=note.note_id, subject_id=subject.subject_id,
                            vector=(1.0,)*dimensions, selected_token_indices=(1,),
                            selected_token_ids=(101,), token_count=3)

        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=WideEncoder()):
            worker.run_worker(state['encodings'][0]['config'])
        generation._collect_encodings(state)
        tracemalloc.start()
        try:
            vectors = generation._vectors(state, [next(iter(state['items']))])
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(tuple(vectors[0]), (1.0,)*dimensions)
        self.assertLess(peak, 12*1024*1024, 'reading one row expanded every other vector')

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
                generation_policy="hierarchy-generation-v3",
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

    def prepare_mixed_bootstrap(self):
        self.configure(
            notes=[
                dict(
                    note_id="n0",
                    text="An unidentified name and two established topics.",
                    origin=dict(prompt_version="ASv6.100"),
                    subjects=[
                        dict(number="1", subject="Unknown", context="Unidentified"),
                        dict(number="2", subject="Known A", context="Established"),
                        dict(number="3", subject="Known B", context="Established"),
                    ],
                )
            ]
        )
        self.automatic_runner()
        needle = 'value={"meaning":"Definition of "+subject}'
        text = self.runner.read_text()
        self.assertIn(needle, text)
        self.runner.write_text(
            text.replace(
                needle,
                'value={"meaning":None if subject=="Unknown" else "Definition of "+subject}',
            )
        )
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        return Path(self.state()["experiments"][0]["experiment"])

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

    def test_prepare_v31_freezes_the_selected_generation_policy(self):
        spec = self.configure(count=3)
        value = json.loads(spec.read_text())
        value["generation_policy"] = "hierarchy-generation-v3.1"
        self.write("hierarchy.json", value)
        self.cli("prepare-hierarchy", "trial", "--spec", spec)
        self.assertEqual(self.state()["generation_policy"], "hierarchy-generation-v3.1")
        self.assertEqual(self.calls(), [])

    def run_cutoff_fixture(self, count=8, policy="hierarchy-generation-v3.1",
                           scores=(0.8, 0.7, 0.6, 0.2)):
        from sse_multivector import hierarchy_generation as generation

        spec = self.configure(count=count)
        value = json.loads(spec.read_text())
        value["generation_policy"] = policy
        self.write("hierarchy.json", value)
        config = json.loads((self.root / "worker.json").read_text())
        config["model"]["dimensions"] = count
        self.write("worker.json", config)
        self.automatic_runner()
        self.cli("prepare-hierarchy", "trial", "--spec", spec)
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch("sse_multivector.worker.OfficialSseEncoder",
                  return_value=CutoffFixtureEncoder(count, scores)),
        ):
            result = generation.run(self.root / "trial")
        return self.state(), result

    def test_v31_only_consolidates_passing_pairs_and_reports_discarded_notes(self):
        state, result = self.run_cutoff_fixture()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(state["experiments"][1]["inputs"]), 2)
        self.assertEqual(len(state["nodes"]), 2)
        self.assertEqual(state["families"][0]["rounds"][0]["cutoff"], 0.66)
        self.assertEqual(result["notes_not_in_hierarchy"], ["n4", "n5", "n6", "n7"])
        self.assertEqual(len(self.calls()), 10)
        self.cli("advance-hierarchy", "trial", "--comment", "Validate completed V3.1")
        self.assertEqual(len(self.calls()), 10)

    def test_v31_carries_a_lone_unpaired_topic_without_a_failed_score(self):
        state, result = self.run_cutoff_fixture(count=9)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(state["nodes"]), 3)
        self.assertTrue(any(n["original_ids"] == ["L00009"] for n in state["nodes"]))
        self.assertEqual(state["families"][0]["rounds"][0]["unpaired"], ["L00009"])

    def test_v3_still_consolidates_every_pair_with_the_same_vectors(self):
        state, result = self.run_cutoff_fixture(policy="hierarchy-generation-v3")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(state["experiments"][1]["inputs"]), 4)
        self.assertEqual(len(state["nodes"]), 4)
        self.assertNotIn("cutoff", state["families"][0]["rounds"][0])

    def test_v31_all_rejected_pairs_finish_without_a_consolidation_batch(self):
        state, result = self.run_cutoff_fixture(scores=(0.5, 0.4, 0.3, 0.2))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(state["nodes"], [])
        self.assertEqual(len(state["experiments"]), 1)
        self.assertEqual(result["notes_not_in_hierarchy"], [f"n{i}" for i in range(8)])
        self.assertEqual(len(self.calls()), 8)
        self.cli("advance-hierarchy", "trial", "--comment", "Validate all rejected")

    def test_v31_decay_restarts_for_each_child_family(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.configure(count=32)
        self.write("hierarchy.json", {
            **json.loads(spec.read_text()), "generation_policy": generation.POLICY_V31,
        })
        self.automatic_runner()
        self.cli("prepare-hierarchy", "trial", "--spec", spec)
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch("sse_multivector.worker.OfficialSseEncoder", return_value=FixtureEncoder()),
        ):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["notes_not_in_hierarchy"], [])
        families = self.state()["families"]
        self.assertEqual([r["cutoff"] for r in families[0]["rounds"]], [0.66, 0.53, 0.465])
        self.assertGreater(len(families), 1)
        self.assertTrue(all(f["rounds"][0]["cutoff"] == 0.66 for f in families[1:]))

    def test_v31_frozen_policy_and_cutoff_cannot_be_changed_on_resume(self):
        from sse_multivector import hierarchy_generation as generation

        state, _ = self.run_cutoff_fixture()
        state["families"][0]["rounds"][0]["cutoff"] = 0.4
        with self.assertRaisesRegex(ValueError, "cutoff or selected pairs changed"):
            generation.check_state(state)
        state["generation_policy"] = generation.POLICY
        with self.assertRaisesRegex(ValueError, "saved controls differ"):
            generation.check_state(state)

    def test_v31_cutoff_includes_the_exact_boundary_and_stays_above_floor(self):
        from sse_multivector import hierarchy_generation as generation

        family = dict(id="F00000", current=["L1", "L2", "L3", "L4"], rounds=[])
        state = dict(generation_policy=generation.POLICY_V31)
        round_ = generation._pairing_round(state, family, [("L1", "L2", 0.66),
                                                          ("L3", "L4", 0.659999)])
        self.assertEqual(round_["cases"], {"F00000-P00000": ["L1", "L2"]})
        family["rounds"] = [None] * 10
        late = generation._pairing_round(state, family, [("L1", "L2", 0.4),
                                                        ("L3", "L4", 0.41)])
        self.assertGreater(late["cutoff"], 0.4)
        self.assertEqual(late["cases"], {"F00000-P00001": ["L3", "L4"]})

    def test_existing_saved_graph_readers_accept_v31_nodes(self):
        state, _ = self.run_cutoff_fixture()
        before = (self.root / "trial/state.json").read_bytes()
        self.cli("export-canonical-viewer", "trial", "--output", "view")
        self.write("compare-source.json", dict(
            schema_version=2, corpus="notes.json",
            canonical_states=dict(current=dict(trial="trial/state.json")),
            pairs=[dict(id="one", local=dict(note_id="n4", number="1"),
                        canonical=dict(state="current", id=state["nodes"][0]["id"]),
                        review={})],
        ))
        spec = json.loads((self.root / "bootstrap.json").read_text())
        spec["dataset"] = dict(adapter="hierarchy_node_pairs", path="compare-source.json")
        spec["runner"]["output_schema"] = json.loads((PROJECT /
            "sse_multivector/shr_single_pair/Hierarchy-compare-v4.output.schema.json").read_text())
        self.write("compare-spec.json", spec)
        self.cli("prepare", "compare", "--spec", self.root / "compare-spec.json")
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)
        self.assertEqual(len(self.calls()), 10)

    def test_v31_reuses_native_answers_in_a_new_construction(self):
        from sse_multivector import hierarchy_generation as generation

        self.run_cutoff_fixture()
        calls = len(self.calls())
        self.cli("prepare-hierarchy", "reuse", "--spec", self.root / "hierarchy.json")
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch("sse_multivector.worker.OfficialSseEncoder",
                  return_value=CutoffFixtureEncoder(8)),
        ):
            result = generation.run(self.root / "reuse")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["notes_not_in_hierarchy"], ["n4", "n5", "n6", "n7"])
        self.assertEqual(len(self.calls()), calls)

    def configure_v32(self, count=3, policy="hierarchy-generation-v3.2",
                      title="Café coffee", meaning="Coffee served as a beverage."):
        spec = self.configure(count=count)
        bootstrap = json.loads((self.root / "bootstrap.json").read_text())
        bootstrap["prompt"] = dict(
            id="Hierarchy-bootstrap-v133",
            path=str(PROJECT / "sse_multivector/shr_single_pair/Hierarchy-bootstrap-v133.md"),
        )
        bootstrap["runner"]["output_schema"] = json.loads((PROJECT /
            "sse_multivector/shr_single_pair/Hierarchy-bootstrap-v130.output.schema.json").read_text())
        self.write("bootstrap.json", bootstrap)
        self.write("hierarchy.json", {
            **json.loads(spec.read_text()), "generation_policy": policy,
        })
        response = dict(
            ambiguities=[], resolutions=[], meaning=meaning, title=title,
            evidence=[] if meaning is None else [dict(quote="Original post", supports=meaning,
                                                     inference=None)],
        )
        # Bind the controlled external producer into its frozen executable.
        # Shared queue workers must not depend on an invocation's ambient response override.
        needle = 'if stage == "prompt":\n'
        code = ('if "ambiguities" in request.get("schema", {}).get("properties", {}):\n'
                '    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"] = ' + repr(json.dumps(response)) + '\n'
                'elif stage == "prompt":\n'
                '    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"] = ' +
                repr(json.dumps(dict(title="Coffee group", meaning="Coffee beverages."))) + '\n')
        self.runner.write_text(self.runner.read_text().replace(needle, code + needle))
        return spec

    def collect_title_bootstrap(self):
        experiment = self.state()["experiments"][0]["experiment"]
        self.cli("run", experiment)
        self.cli("advance-hierarchy", "trial", "--comment", "Collect Bootstrap title and meaning")

    def prepare_v4_root_probe(self, count=21, unique=False, encode=True, null_first=False):
        spec = self.configure_v32(count=count)
        if unique:
            code = '''if "ambiguities" in properties:
    import hashlib
    value=json.loads(os.environ["FAKE_RUNNER_PROMPT_RESPONSE"])
    value["title"]="Topic "+hashlib.sha256(prompt.encode()).hexdigest()[:12]
    value["meaning"]="Definition of "+value["title"]
    value["evidence"][0]["supports"]=value["meaning"]
    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"]=json.dumps(value)
'''
            self.runner.write_text(self.runner.read_text().replace(
                '\nif stage == "prompt":\n', '\n'+code+'if stage == "prompt":\n'))
        if null_first:
            code = '''if "ambiguities" in properties and "Original post 0" in prompt:
    value=json.loads(os.environ["FAKE_RUNNER_PROMPT_RESPONSE"])
    value.update(title=None, meaning=None, evidence=[])
    os.environ["FAKE_RUNNER_PROMPT_RESPONSE"]=json.dumps(value)
'''
            self.runner.write_text(self.runner.read_text().replace(
                '\nif stage == "prompt":\n', '\n'+code+'if stage == "prompt":\n'))
        self.cli("prepare-hierarchy", "trial", "--spec", spec)
        self.collect_title_bootstrap()
        if encode:
            self.encode_pending()
        binary = self.root / "hdbscan-fixture"
        binary.write_text('''#!/usr/bin/env python3
import json, sys
r=json.load(open(sys.argv[1]))
ids=[i["opaque_id"] for i in r["inputs"]]
groups=[ids[i:i+3] for i in range(0,len(ids)-2,3)]
print(json.dumps({"schema_version":1,"candidate_identity":"hdbscan-explicit-config-v1",
 "artifact":{"canonical_input_ids":sorted(ids),
 "canonical_configuration_json":json.dumps(r["hdbscan_configuration"]),
 "result":{"fine_output":{"segments":groups}},
 "manifest":{"parameters":r["hdbscan_configuration"],
 "algorithm_version":"hdbscan-star-exact-angular-v1",
 "fine_output_selector_version":"hdbscan-clusters-members-v1",
 "source_vector_manifest_sha256":r["source_vector_manifest_sha256"],
 "normalized_vector_sha256":r["normalized_vector_sha256"]}}}))
''')
        binary.chmod(0o755)
        consolidation = json.loads((self.root / "consolidation.json").read_text())
        consolidation["prompt"] = dict(id="Hierarchy-consolidated-grouped-v1", path=str(
            PROJECT / "sse_multivector/shr_single_pair/Hierarchy-consolidated-grouped-v1.md"))
        self.write("group-consolidation.json", consolidation)
        cfg = json.loads((self.root / "hierarchy.json").read_text())
        cfg.update(generation_policy="hierarchy-generation-v4-roots",
                   bootstrap_hierarchy="trial/state.json", hdbscan_binary=str(binary),
                   consolidation_spec="group-consolidation.json")
        return self.write("v4.json", cfg)

    def test_v4_root_probe_reuses_saved_bootstrap_and_vectors(self):
        spec = self.prepare_v4_root_probe()
        prior_calls = self.calls()
        source = self.state()
        self.cli("prepare-hierarchy", "v4", "--spec", spec)
        state = json.loads((self.root / "v4/state.json").read_text())
        self.assertEqual(state["generation_policy"], "hierarchy-generation-v4-roots")
        self.assertEqual(state["experiments"][0], source["experiments"][0])
        self.assertEqual(state["encodings"], source["encodings"])
        self.assertEqual(self.calls(), prior_calls)

    def test_v5_reuses_completed_bootstrap_when_only_deadline_is_extended(self):
        base = json.loads(self.spec.read_text())
        base['runner']['timeout_seconds'] = 600
        self.spec.write_text(json.dumps(base))
        spec = self.prepare_v41(count=9)
        source = self.state()
        prior_calls = self.calls()
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5'
        bootstrap = json.loads((self.root / 'bootstrap.json').read_text())
        old_timeout = bootstrap['runner']['timeout_seconds']
        bootstrap['runner']['timeout_seconds'] = old_timeout + 3600
        self.write('bootstrap-longer.json', bootstrap)
        cfg['bootstrap_spec'] = 'bootstrap-longer.json'
        changed = self.write('longer.json', cfg)
        self.cli('prepare-hierarchy', 'longer', '--spec', changed)
        state = json.loads((self.root / 'longer/state.json').read_text())
        self.assertEqual(state['experiments'][0], source['experiments'][0])
        self.assertEqual(state['vectors'], source['vectors'])
        self.assertEqual(state['bootstrap_spec']['runner']['timeout_seconds'], old_timeout + 3600)
        self.assertEqual(source['bootstrap_spec']['runner']['timeout_seconds'], old_timeout)
        for field, value in [('timeout_seconds', old_timeout / 2), ('model', 'different/model')]:
            with self.subTest(field=field):
                incompatible = json.loads(json.dumps(bootstrap))
                incompatible['runner'][field] = value
                self.write('bootstrap-incompatible.json', incompatible)
                cfg['bootstrap_spec'] = 'bootstrap-incompatible.json'
                changed = self.write('incompatible.json', cfg)
                result = self.cli('prepare-hierarchy', 'incompatible', '--spec', changed, ok=False)
                self.assertIn('matching saved Bootstrap', result.stderr)
        self.assertEqual(self.calls(), prior_calls)

    def test_v5_reuses_completed_bootstrap_before_encoding_is_finished(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare_v41(count=9, encode=False)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5'
        spec = self.write('v5.json', cfg)
        source_path = self.root / 'trial/state.json'
        before = source_path.read_bytes()
        source = self.state()
        self.assertTrue(source['experiments'][0]['complete'])
        self.assertFalse(source['encodings'][0]['complete'])
        prior_calls = self.calls()
        self.cli('prepare-hierarchy', 'v4', '--spec', spec)
        prepared = json.loads((self.root / 'v4/state.json').read_text())
        self.assertEqual(prepared['experiments'][0], source['experiments'][0])
        self.assertEqual(prepared['encodings'], [])
        self.assertEqual(self.calls(), prior_calls)
        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=FixtureEncoder()), \
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log)):
            result = generation.run(self.root / 'v4')
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(source_path.read_bytes(), before)

    def test_v4_root_probe_repeats_groups_and_counts_distinct_note_loss(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare_v4_root_probe()
        self.cli("prepare-hierarchy", "v4", "--spec", spec)
        with patch("sse_multivector.worker.OfficialSseEncoder", return_value=FixtureEncoder()), \
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log)):
            result = generation.run(self.root / "v4")
        state = json.loads((self.root / "v4/state.json").read_text())
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(state["nodes"]), 2)
        self.assertEqual(len(state["families"]), 1)
        self.assertTrue(all(not n["parents"] for n in state["nodes"]))
        self.assertEqual([(r["input_nodes"], r["groups"], r["notes_after"])
                          for r in result["hdbscan_rounds"]], [(21, 7, 21), (7, 2, 18)])
        self.assertEqual(len(result["notes_not_in_hierarchy"]), 3)
        for experiment in state["experiments"][1:]:
            for payload in experiment["inputs"].values():
                self.assertEqual(len(json.loads(payload["INPUT_JSON"])["nodes"]), 3)
        generation.check_state(state)

    def test_v4_root_probe_rejects_changed_cluster_evidence(self):
        spec = self.prepare_v4_root_probe(count=3)
        self.cli("prepare-hierarchy", "v4", "--spec", spec)
        self.cli("advance-hierarchy", "v4", "--comment", "Prepare original group")
        state = json.loads((self.root / "v4/state.json").read_text())
        path = Path(state["families"][0]["rounds"][0]["hdbscan"]["result"])
        value = json.loads(path.read_text())
        value["artifact"]["result"]["fine_output"]["segments"] = []
        path.write_text(json.dumps(value))
        prior = self.calls()
        result = self.cli("advance-hierarchy", "v4", "--comment", "Reject changed groups", ok=False)
        self.assertIn("saved HDBSCAN evidence changed", result.stderr)
        self.assertEqual(self.calls(), prior)

    def prepare_v41(self, count=43, unique=False, tied=False, encode=True, null_first=False):
        spec = self.prepare_v4_root_probe(count=count, unique=unique, encode=encode,
                                          null_first=null_first)
        binary = self.root / "hdbscan-fixture"
        binary.write_text('''#!/usr/bin/env python3
import json, sys
r=json.load(open(sys.argv[1]))
ids=sorted(i["opaque_id"] for i in r["inputs"])
groups=[ids[i:i+3] for i in range(0,len(ids)-2,3)]
n=len(ids); k=len(groups)
leaves=[n+k-1+i for i in range(k)]
edges=[]
for i in range(k-1):
    children=([n+i+1,leaves[k-i-1]] if i<k-2 else leaves[:2])
    for child in children:
        edges.append({"parent":n+i,"child":child,"child_size":3,
                      "lambda":1/((k-i-1)/10)})
clusters=[{"id":leaf,"members":[ids.index(x) for x in group],"stability":1}
          for leaf,group in zip(leaves,groups)]
print(json.dumps({"schema_version":1,"candidate_identity":"hdbscan-explicit-config-v1",
 "artifact":{"canonical_input_ids":ids,
 "canonical_configuration_json":json.dumps(r["hdbscan_configuration"]),
 "result":{"canonical_unique_ids":ids,"alias_groups":[[i] for i in ids],
 "algorithm_result":{"vector_count":n,"clusters":clusters,"condensed_tree":edges},
 "fine_output":{"segments":groups}},
 "manifest":{"parameters":r["hdbscan_configuration"],
 "algorithm_version":"hdbscan-star-exact-angular-v1",
 "fine_output_selector_version":"hdbscan-clusters-members-v1",
 "source_vector_manifest_sha256":r["source_vector_manifest_sha256"],
 "normalized_vector_sha256":r["normalized_vector_sha256"]}}}))
''')
        if tied:
            binary.write_text(binary.read_text().replace('1/((k-i-1)/10)', '1'))
        cfg = json.loads(spec.read_text())
        cfg["generation_policy"] = "hierarchy-generation-v4.1"
        return self.write("v41.json", cfg)

    def test_v41_keeps_one_tree_and_names_immediate_children_bottom_up(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare_v41()
        source = self.state()
        self.cli("prepare-hierarchy", "v41", "--spec", spec)
        result = json.loads(self.cli("run-hierarchy", "v41").stdout)
        state = json.loads((self.root / "v41/state.json").read_text())
        self.assertEqual(result["status"], "complete")
        self.assertEqual(state["encodings"], source["encodings"])
        self.assertEqual(len(result["hdbscan_rounds"]), 1)
        self.assertEqual(len(state["nodes"]), 16)  # 14 groups, two displayed joins.
        roots = [n for n in state["nodes"] if not n["parents"]]
        self.assertEqual(len(roots), 6)
        parents = {p for n in state["nodes"] for p in n["parents"]}
        leaves = [n for n in state["nodes"] if n["id"] not in parents]
        self.assertEqual(len(leaves), 14)
        self.assertTrue(all(len(n["original_ids"]) == 3 for n in leaves))
        self.assertEqual(len(result["notes_not_in_hierarchy"]), 1)
        for parent in parents:
            self.assertLessEqual(sum(parent in n["parents"] for n in state["nodes"]), 6)
        payloads = [json.loads(p["INPUT_JSON"]) for r in state["experiments"][1:]
                    for p in r["inputs"].values()]
        self.assertEqual(sorted(len(p["nodes"]) for p in payloads), [3]*14+[4, 6])
        self.assertTrue(all("parent" not in p for p in payloads))
        self.assertTrue(all(n["title"] == "Coffee group" for p in payloads
                            if len(p["nodes"]) != 3 for n in p["nodes"]))
        generation.check_state(state)

    def test_v41_passes_provider_attempt_limit_to_native_teacher_batches(self):
        spec = self.prepare_v41()
        self.cli("prepare-hierarchy", "v41", "--spec", spec)
        result = json.loads(self.cli("run-hierarchy", "v41", "--max-provider-attempts", "2").stdout)
        self.assertEqual(result['status'], 'complete')
        settings = json.loads((self.root / 'v41/execution-settings.json').read_text())
        self.assertEqual(settings['max_provider_attempts'], 2)
        state = json.loads((self.root / 'v41/state.json').read_text())
        for record in state['experiments'][1:]:
            rows = [json.loads(line) for line in
                    (Path(record['experiment']) / 'execution-settings.jsonl').read_text().splitlines()]
            self.assertTrue(rows)
            self.assertTrue(all(row['max_provider_attempts'] == 2 for row in rows))

    def test_v41_resume_records_removed_provider_limit_without_rewriting_initial_settings(self):
        spec = self.prepare_v41()
        self.cli('prepare-hierarchy', 'v41', '--spec', spec)
        self.cli('run-hierarchy', 'v41', '--max-provider-attempts', '2')
        settings = self.root / 'v41/execution-settings.json'
        before = settings.read_bytes()
        self.cli('run-hierarchy', 'v41')
        self.assertEqual(settings.read_bytes(), before)
        rows = [json.loads(line) for line in
                (self.root / 'v41/execution-settings.jsonl').read_text().splitlines()]
        self.assertEqual(rows[-1]['max_provider_attempts'], None)

    def test_v41_source_upgrade_moves_the_hdbscan_helper_binding(self):
        from sse_multivector import hierarchy_hdbscan

        spec = self.prepare_v41()
        self.cli('prepare-hierarchy', 'v41', '--spec', spec)
        path = self.root / 'v41/state.json'
        state = json.loads(path.read_text())
        current = Path(hierarchy_hdbscan.__file__).resolve()
        archived = self.root / 'archived/sse_multivector/hierarchy_hdbscan.py'
        archived.parent.mkdir(parents=True)
        archived.write_bytes(current.read_bytes())
        state['sources'][str(archived)] = state['sources'].pop(str(current))
        path.write_text(json.dumps(state))
        result = json.loads(self.cli('run-hierarchy', 'v41', '--runner-upgrade-reason',
                                     'Approved recovery worktree migration').stdout)
        self.assertEqual(result['status'], 'complete')
        state = json.loads(path.read_text())
        self.assertIn(str(current), state['sources'])
        self.assertNotIn(str(archived), state['sources'])
        self.assertEqual(state['source_upgrades'][0]['before'],
                         {str(archived): hashlib.sha256(archived.read_bytes()).hexdigest()})

    def test_bootstrap_diagnostic_errors_do_not_block_meanings_or_encoding(self):
        spec = self.configure_v32()
        self.runner.write_text(self.runner.read_text().replace(
            '"quote": "Original post"', '"quote": "Words absent from the post"'))
        self.cli('prepare-hierarchy', 'trial', '--spec', spec)
        experiment = self.state()['experiments'][0]['experiment']
        self.cli('run', experiment)
        result = json.loads(self.cli('advance-hierarchy', 'trial', '--comment',
                                     'Retain diagnostics without blocking').stdout)
        state = self.state()
        self.assertEqual(len(state['encodings']), 1)
        self.assertTrue(state['experiments'][0]['complete'])
        self.assertEqual(len(result['diagnostic_errors']), 3)
        self.assertTrue(all(o['meaning'] == 'Coffee served as a beverage.' for o in state['originals']))

    def _assert_section_policy_controls(self, policy, min_samples, min_cluster_size):
        from sse_multivector import hierarchy_generation as generation
        from sse_multivector import hierarchy_hdbscan as hdbscan

        spec = self.prepare_v41(count=9)
        binary = self.root / "hdbscan-fixture"
        binary.write_text(binary.read_text().replace(
            'groups=[ids[i:i+3] for i in range(0,len(ids)-2,3)]',
            'size=r["hdbscan_configuration"]["min_cluster_size"]\n'
            'groups=[ids[i:i+size] for i in range(0,len(ids)-size+1,size)]'
        ).replace('"child_size":3', '"child_size":size'))
        cfg = json.loads(spec.read_text())
        cfg["generation_policy"] = policy
        spec = self.write("v42.json", cfg)
        prior = self.calls()
        self.cli("prepare-hierarchy", "v42", "--spec", spec)
        self.assertEqual(self.calls(), prior)
        result = json.loads(self.cli("run-hierarchy", "v42").stdout)
        state = json.loads((self.root / "v42/state.json").read_text())
        round_ = state["families"][0]["rounds"][0]
        request = json.loads(Path(round_["hdbscan"]["request"]).read_text())
        self.assertEqual(request["hdbscan_configuration"], dict(
            min_samples=min_samples, min_cluster_size=min_cluster_size,
            selection_method="excess_of_mass"))
        self.assertEqual(result["generation_policy"], policy)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(result["hdbscan_rounds"]), 1)
        expected_groups = [min_cluster_size] * (9 // min_cluster_size)
        self.assertEqual(result["hdbscan_rounds"][0]["group_sizes"], expected_groups)
        self.assertEqual(len(state["nodes"]), len(expected_groups))
        self.assertTrue(all(len(n["original_ids"]) == min_cluster_size
                            for n in state["nodes"]))
        generation.check_state(state)
        legacy = dict(state, generation_policy="hierarchy-generation-v4.1")
        old_request, _ = hdbscan.request_for(legacy, round_["current"],
                                           generation._vectors(state, round_["current"]))
        self.assertEqual(old_request["hdbscan_configuration"]["min_cluster_size"], 2)
        state["generation_policy"] = "hierarchy-generation-v4.1"
        with self.assertRaisesRegex(ValueError, "frozen hierarchy definition"):
            generation.check_state(state)

    def test_v42_uses_cluster_size_four_through_native_construction(self):
        self._assert_section_policy_controls("hierarchy-generation-v4.2", 3, 4)

    def test_v43_uses_samples_four_and_cluster_size_two_through_native_construction(self):
        self._assert_section_policy_controls("hierarchy-generation-v4.3", 4, 2)

    def test_v44_uses_samples_four_and_cluster_size_four_through_native_construction(self):
        self._assert_section_policy_controls("hierarchy-generation-v4.4", 4, 4)

    def test_v42_reuses_v41_bootstrap_answers_and_original_vectors(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare_v41(count=9)
        self.cli("prepare-hierarchy", "v41", "--spec", spec)
        self.cli("run-hierarchy", "v41")
        source = json.loads((self.root / "v41/state.json").read_text())
        cfg = json.loads(spec.read_text())
        cfg.update(generation_policy="hierarchy-generation-v4.2",
                   bootstrap_hierarchy="v41/state.json")
        spec = self.write("v42-from-v41.json", cfg)
        prior = self.calls()
        self.cli("prepare-hierarchy", "v42", "--spec", spec)
        state = json.loads((self.root / "v42/state.json").read_text())
        self.assertEqual(self.calls(), prior)
        self.assertEqual(state["experiments"], [source["experiments"][0]])
        self.assertEqual(state["encodings"], source["encodings"])
        self.assertEqual(state["vectors"], source["vectors"])
        self.assertEqual(state["families"], [])
        self.assertEqual(state["nodes"], [])
        generation.check_state(state)

    def test_v41_rejects_changed_section_edges_and_retains_native_reuse(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare_v41()
        self.cli("prepare-hierarchy", "v41", "--spec", spec)
        self.cli("run-hierarchy", "v41")
        before = self.calls()
        self.cli("prepare-hierarchy", "v41-repeat", "--spec", spec)
        self.cli("run-hierarchy", "v41-repeat")
        self.assertEqual(self.calls(), before)
        state = json.loads((self.root / "v41/state.json").read_text())
        node = next(n for n in state["nodes"] if n["parents"])
        node["parents"] = []
        with self.assertRaisesRegex(ValueError, "HDBSCAN section"):
            generation.check_state(state)

    def test_v41_can_prepare_bootstrap_without_a_previous_hierarchy(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare_v41(count=7)
        cfg = json.loads(spec.read_text())
        del cfg["bootstrap_hierarchy"]
        self.write("fresh.json", cfg)
        self.cli("prepare-hierarchy", "fresh", "--spec", "fresh.json")
        state = json.loads((self.root / "fresh/state.json").read_text())
        self.assertEqual(state["status"], "bootstrap")
        self.assertNotIn("bootstrap_hierarchy", state)
        with patch("sse_multivector.worker.OfficialSseEncoder", return_value=FixtureEncoder()), \
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log)):
            result = generation.run(self.root / "fresh")
        self.assertEqual(result["status"], "complete")
        state = json.loads((self.root / "fresh/state.json").read_text())
        self.assertEqual(len(state["encodings"]), 1)
        self.assertEqual(len(state["nodes"]), 2)
        generation.check_state(state)

    def test_v41_ready_section_advances_before_unrelated_groups_finish(self):
        spec = self.prepare_v41(unique=True)
        self.cli("prepare-hierarchy", "v41", "--spec", spec)
        self.cli("advance-hierarchy", "v41", "--comment", "Prepare original groups")
        state = json.loads((self.root / "v41/state.json").read_text())
        section = next(s for s in state["hdbscan_sections"]["sections"] if len(s["children"]) == 4)
        self.cli("run", state["experiments"][1]["experiment"],
                 *[a for c in section["children"] for a in ("--only", f"H{c:06d}")])
        self.cli("advance-hierarchy", "v41", "--comment", "Collect four independent groups")
        state = json.loads((self.root / "v41/state.json").read_text())
        self.assertFalse(state["experiments"][1]["complete"])
        self.assertEqual(len(state["nodes"]), 4)
        self.assertEqual(len(state["experiments"]), 3)
        self.assertEqual(len(state["experiments"][2]["inputs"]), 1)
        payload = json.loads(next(iter(state["experiments"][2]["inputs"].values()))["INPUT_JSON"])
        self.assertEqual(len(payload["nodes"]), 4)
        self.cli("run-hierarchy", "v41")
        count = len(self.calls())
        result = json.loads(self.cli("run-hierarchy", "v41").stdout)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(self.calls()), count)

    def test_v41_impossible_tied_cut_blocks_without_calls_or_runner_backoff(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare_v41(tied=True)
        self.cli("prepare-hierarchy", "v41", "--spec", spec)
        prior = self.calls()
        result = json.loads(self.cli("run-hierarchy", "v41", ok=False).stdout)
        self.assertEqual(result["status"], "blocked_hdbscan")
        self.assertEqual(self.calls(), prior)
        self.assertIn("tied split", result["unresolved"][0]["error"])
        self.assertFalse((self.root / "v41/runner-backoff.jsonl").exists())
        state = json.loads((self.root / "v41/state.json").read_text())
        generation.check_state(state)
        result = json.loads(self.cli("advance-hierarchy", "v41", "--comment", "Keep evidence").stdout)
        self.assertEqual(result["status"], "blocked_hdbscan")

    def test_v32_generated_title_drives_sse_and_browsing_preserving_original_subject(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure_v32())
        self.collect_title_bootstrap()
        state = self.state()
        self.assertEqual(state["originals"][0]["subject"], "Topic 0")
        self.assertEqual(state["originals"][0].get("title"), "Café coffee")
        request = json.loads((Path(state["encodings"][0]["config"]).parent /
                              "request.json").read_text())
        self.assertEqual(len(request["notes"]), 1)
        self.assertEqual(request["notes"][0]["text"], "Café coffee\n\nCoffee served as a beverage.")
        self.assertEqual(request["notes"][0]["subjects"][0]["byte_spans"],
                         [[0, len("Café coffee".encode())]])
        self.encode_pending()
        self.cli("export-canonical-viewer", "trial", "--output", "view")
        view = json.loads((self.root / "view/hierarchy.json").read_text())
        self.assertTrue(all(n["label"].startswith("Café coffee (")
                            for n in view["nodes"] if n["node_id"] != "VIEW_ROOT"))
        self.cli("advance-hierarchy", "trial", "--comment", "Validate completed V3.2")
        self.assertEqual(len(self.calls()), 3)
        from sse_multivector import hierarchy_generation as generation

        state = self.state()
        state["originals"][0]["title"] = "Changed title"
        with self.assertRaisesRegex(ValueError, "title differs from native Bootstrap"):
            generation.check_state(state)
        state = self.state()
        state["items"]["L00001"]["subject"] = "Topic 0"
        with self.assertRaisesRegex(ValueError, "invalid original local L1 item"):
            generation.check_state(state)
        self.cli("prepare-hierarchy", "reuse", "--spec", self.root / "hierarchy.json")
        with patch("sse_multivector.worker.OfficialSseEncoder", return_value=FixtureEncoder()):
            result = generation.run(self.root / "reuse")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(self.calls()), 3)
        reused = json.loads((self.root / "reuse/state.json").read_text())
        self.assertTrue(all(n["subject"] == "Café coffee" for n in reused["nodes"]))

    def test_v32_consolidation_receives_generated_titles_and_uses_v31_cutoff(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure_v32(count=7))
        self.collect_title_bootstrap()
        self.encode_pending()
        state = self.state()
        round_ = state["families"][0]["rounds"][0]
        self.assertEqual(round_["cutoff"], 0.66)
        self.assertEqual(round_["unpaired"], ["L00007"])
        payloads = [json.loads(v["INPUT_JSON"])
                    for v in state["experiments"][1]["inputs"].values()]
        self.assertEqual(len(payloads), 3)
        self.assertTrue(all(n["title"] == "Café coffee"
                            for p in payloads for n in p["nodes"]))
        self.cli("run", state["experiments"][1]["experiment"])
        self.cli("advance-hierarchy", "trial", "--comment", "Collect pair titles")
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual([n["subject"] for n in state["nodes"]],
                         ["Coffee group"] * 3 + ["Café coffee"])
        # Identical pair inputs share one native answer within this batch.
        self.assertEqual(len(self.calls()), 8)

    def test_v32_null_meaning_keeps_null_title_and_never_encodes_it(self):
        self.cli("prepare-hierarchy", "trial", "--spec",
                 self.configure_v32(count=1, title=None, meaning=None))
        self.collect_title_bootstrap()
        state = self.state()
        self.assertEqual(state["status"], "blocked_bootstrap")
        self.assertIn("title", state["originals"][0])
        self.assertIsNone(state["originals"][0]["title"])
        self.assertEqual(state["encodings"], [])
        self.assertEqual(state["nodes"], [])
        self.cli("advance-hierarchy", "trial", "--comment", "Validate null Bootstrap")
        self.assertEqual(len(self.calls()), 1)

    def test_v31_keeps_original_subject_when_bootstrap_also_returns_title(self):
        self.cli("prepare-hierarchy", "trial", "--spec",
                 self.configure_v32(count=1, policy="hierarchy-generation-v3.1"))
        self.collect_title_bootstrap()
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["originals"][0]["subject"], "Topic 0")
        self.assertNotIn("title", state["originals"][0])
        self.assertEqual(state["nodes"][0]["subject"], "Topic 0")

    def test_v32_rejects_old_bootstrap_or_missing_title_schema_before_inference(self):
        spec = self.configure(count=1)
        self.write("hierarchy.json", {
            **json.loads(spec.read_text()), "generation_policy": "hierarchy-generation-v3.2",
        })
        result = self.cli("prepare-hierarchy", "trial", "--spec", spec, ok=False)
        self.assertIn("requires Hierarchy-bootstrap-v133", result.stderr)
        bootstrap = json.loads((self.root / "bootstrap.json").read_text())
        bootstrap["prompt"] = dict(id="Hierarchy-bootstrap-v133", path=str(PROJECT /
            "sse_multivector/shr_single_pair/Hierarchy-bootstrap-v133.md"))
        self.write("bootstrap.json", bootstrap)
        result = self.cli("prepare-hierarchy", "trial", "--spec", spec, ok=False)
        self.assertIn("requires the Bootstrap title output schema", result.stderr)
        bootstrap["runner"]["output_schema"] = json.loads((self.root / "consolidation.json")
                                                          .read_text())["runner"]["output_schema"]
        self.write("bootstrap.json", bootstrap)
        result = self.cli("prepare-hierarchy", "trial", "--spec", spec, ok=False)
        self.assertIn("requires the Bootstrap title output schema", result.stderr)
        self.assertFalse((self.root / "trial").exists())
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

    def consolidate_long_meaning(self, count=10):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=count))
        self.bootstrap()
        self.encode_pending()
        experiment = self.state()["experiments"][-1]["experiment"]
        self.cli(
            "run",
            experiment,
            env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(
                dict(title="Combined topic", meaning="word " * 600)
            )},
        )
        self.cli("advance-hierarchy", "trial", "--comment", "Collect long meaning")

    def test_finished_groups_promote_without_encoding_their_meanings(self):
        self.consolidate_long_meaning()
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["nodes"]), 5)
        self.assertEqual(len(state["encodings"]), 1)
        self.assertTrue(state["encodings"][0]["complete"])
        self.assertEqual(state["worker_config"]["model"]["maximum_tokens"], 512)
        self.assertTrue(all(n["meaning"] == "word " * 600 for n in state["nodes"]))

    def test_resume_skips_unused_queued_encoding_without_repeating_answers(self):
        from sse_multivector import hierarchy_generation as generation

        self.consolidate_long_meaning()
        state = self.state()
        # Older constructors queued this job before promoting the final groups.
        # The production planner creates its original request and config here.
        generation._prepare_encoding(
            self.root / "trial", state, state["families"][0]["current"]
        )
        state.update(status="constructing", nodes=[])
        state["families"][0]["complete"] = False
        self.write("trial/state.json", state)
        pending = state["encodings"][-1]
        files = [Path(pending["config"]), Path(pending["config"]).parent / "request.json"]
        before = {p: p.read_bytes() for p in files}
        receipts = {
            Path(r["experiment"]) / "run/results.jsonl":
                (Path(r["experiment"]) / "run/results.jsonl").read_bytes()
            for r in state["experiments"]
        }
        calls = self.calls()

        class LengthCheckedEncoder(FixtureEncoder):
            def encode(self, notes):
                worker.validate_token_lengths(
                    [(n.note_id, len(n.text.split())) for n in notes], maximum_tokens=512
                )
                return super().encode(notes)

        with patch("sse_multivector.worker.OfficialSseEncoder",
                   return_value=LengthCheckedEncoder()):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["execution_status"], "complete")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["encodings"], [])
        after = self.state()
        self.assertEqual(after["encodings"][-1]["skipped"], "no further pairing")
        self.assertFalse(after["encodings"][-1]["complete"])
        self.assertEqual(after["vectors"], state["vectors"])
        self.assertEqual(self.calls(), calls)
        for p, data in {**before, **receipts}.items():
            self.assertEqual(p.read_bytes(), data)

    def test_long_meaning_still_requires_encoding_when_more_pairs_are_needed(self):
        self.consolidate_long_meaning(count=14)
        state = self.state()
        self.assertEqual(state["status"], "constructing")
        self.assertEqual(len(state["families"][0]["current"]), 7)
        pending = state["encodings"][-1]
        self.assertFalse(pending.get("skipped"))

        class LengthCheckedEncoder(FixtureEncoder):
            def encode(self, notes):
                worker.validate_token_lengths(
                    [(n.note_id, len(n.text.split())) for n in notes], maximum_tokens=512
                )
                return super().encode(notes)

        with patch("sse_multivector.worker.OfficialSseEncoder",
                   return_value=LengthCheckedEncoder()):
            with self.assertRaisesRegex(ValueError, "truncation is forbidden"):
                worker.run_worker(pending["config"])

    def test_null_bootstrap_is_omitted_when_note_has_a_defined_l1(self):
        notes = [
            dict(
                note_id="n0",
                text="An unidentified name and an established topic.",
                origin=dict(prompt_version="ASv6.100"),
                subjects=[
                    dict(number="1", subject="Unknown", context="Unidentified"),
                    dict(number="2", subject="Known", context="Established"),
                ],
            )
        ]
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(notes=notes))
        self.automatic_runner()
        text = self.runner.read_text()
        needle = 'value={"meaning":"Definition of "+subject}'
        self.assertIn(needle, text)
        self.runner.write_text(
            text.replace(
                needle,
                'value={"meaning":None if subject=="Unknown" else "Definition of "+subject}',
            )
        )
        experiment = self.state()["experiments"][0]["experiment"]
        self.cli("run", experiment, env={"FAKE_V3": "1"})
        answers = (Path(experiment) / "run/results.jsonl").read_bytes()
        calls = self.calls()
        result = self.cli("advance-hierarchy", "trial", "--comment", "Omit null L1")
        state = self.state()
        self.assertEqual(state["status"], "constructing")
        self.assertEqual(len(state["originals"]), 2)
        self.assertIsNone(state["originals"][0]["meaning"])
        self.assertEqual(state["families"][0]["original_ids"], ["L00002"])
        self.assertEqual(set(state["items"]), {"L00002"})
        self.assertEqual(state.get("unresolved", []), [])
        self.assertEqual(
            [row["case"] for row in json.loads(result.stdout)["skipped_bootstrap"]],
            ["L00001"],
        )
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(state["note_ids"], ["n0"])
        self.assertEqual(state["nodes"][0]["original_ids"], ["L00002"])
        self.assertEqual((Path(experiment) / "run/results.jsonl").read_bytes(), answers)
        self.assertEqual(self.calls(), calls)

    def test_null_bootstrap_keeps_all_entries_and_prevents_root_construction(self):
        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=3))
        self.bootstrap(meaning=None)
        state = self.state()
        self.assertEqual(state["status"], "blocked_bootstrap")
        self.assertEqual(len(state["originals"]), 3)
        self.assertEqual(len(state["unresolved"]), 3)
        self.assertEqual(state["encodings"], [])
        self.assertEqual(state["nodes"], [])

    def test_legacy_null_blocked_checkpoint_resumes_without_new_calls_or_budget_reset(self):
        from sse_multivector import hierarchy_generation as generation

        experiment = self.prepare_mixed_bootstrap()
        budget = self.root / "allowance.json"
        generation.workflow.engine.PersistentAttemptBudget(budget).initialize(100)
        self.cli("run", experiment, "--attempt-budget", budget, env={"FAKE_V3": "1"})
        state = self.state()
        record = state["experiments"][0]
        generation._collect_experiment(record)
        self.assertTrue(record["complete"])

        # Former V3 saved only established meanings before blocking on any null.
        for original in state["originals"]:
            meaning = record["answers"][original["id"]]["output"]["meaning"]
            if meaning is not None:
                original["meaning"] = meaning
        state.update(
            status="blocked_bootstrap",
            unresolved=[
                dict(
                    local=state["originals"][0]["local"],
                    case="L00001",
                    experiment=str(experiment),
                    reason="null Bootstrap meaning",
                )
            ],
        )
        self.write("trial/state.json", state)
        generation.check_state(state)
        receipts = (experiment / "run/results.jsonl").read_bytes()
        allowance = budget.read_bytes()
        calls = self.calls()
        self.assertEqual(json.loads(allowance)["used"], 3)

        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            result = generation.run(self.root / "trial", budget)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["execution_status"], "complete")
        self.assertEqual([row["case"] for row in result["skipped_bootstrap"]], ["L00001"])
        state = self.state()
        self.assertEqual(state["note_ids"], ["n0"])
        self.assertEqual(len(state["originals"]), 3)
        self.assertEqual(state["families"][0]["original_ids"], ["L00002", "L00003"])
        self.assertEqual(result["unresolved"], [])
        self.assertEqual((experiment / "run/results.jsonl").read_bytes(), receipts)
        self.assertEqual(budget.read_bytes(), allowance)
        self.assertEqual(self.calls(), calls)

        completed = (self.root / "trial/state.json").read_bytes()
        self.assertEqual(generation.run(self.root / "trial", budget)["status"], "complete")
        self.assertEqual((self.root / "trial/state.json").read_bytes(), completed)
        self.assertEqual((experiment / "run/results.jsonl").read_bytes(), receipts)
        self.assertEqual(budget.read_bytes(), allowance)
        self.assertEqual(self.calls(), calls)

    def test_missing_defined_original_cannot_be_omitted_like_a_null_bootstrap(self):
        from sse_multivector import hierarchy_generation as generation

        experiment = self.prepare_mixed_bootstrap()
        self.cli("run", experiment, env={"FAKE_V3": "1"})
        self.cli("advance-hierarchy", "trial", "--comment", "Collect mixed meanings")
        self.encode_pending()
        state = self.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(state["families"][0]["original_ids"], ["L00002", "L00003"])

        del state["originals"][1]["meaning"]
        item = state["items"].pop("L00002")
        state["vectors"].pop(item["vector_key"])
        state["nodes"] = [node for node in state["nodes"] if node["item"] != "L00002"]
        state["families"][0]["original_ids"].remove("L00002")
        state["families"][0]["current"].remove("L00002")
        self.write("trial/state.json", state)
        before = (self.root / "trial/state.json").read_bytes()
        calls = self.calls()

        with self.subTest(check="state validation"):
            with self.assertRaises(ValueError):
                generation.check_state(state)
        with self.subTest(check="native advancement"):
            result = self.cli(
                "advance-hierarchy", "trial", "--comment", "Reject missing meaning", ok=False
            )
            self.assertIn("meaning", result.stderr)
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)
        self.assertEqual(self.calls(), calls)

    def test_nonnull_bootstrap_cannot_be_marked_null_to_remove_its_original(self):
        from sse_multivector import hierarchy_generation as generation

        experiment = self.prepare_mixed_bootstrap()
        self.cli("run", experiment, env={"FAKE_V3": "1"})
        self.cli("advance-hierarchy", "trial", "--comment", "Collect mixed meanings")
        self.encode_pending()
        state = self.state()
        state["originals"][1]["meaning"] = None
        item = state["items"].pop("L00002")
        state["vectors"].pop(item["vector_key"])
        state["nodes"] = [node for node in state["nodes"] if node["item"] != "L00002"]
        state["families"][0]["original_ids"].remove("L00002")
        state["families"][0]["current"].remove("L00002")
        self.write("trial/state.json", state)
        before = (self.root / "trial/state.json").read_bytes()

        with self.assertRaisesRegex(ValueError, "original meaning differs from native Bootstrap"):
            generation.check_state(state)
        result = self.cli(
            "advance-hierarchy", "trial", "--comment", "Reject forged null", ok=False
        )
        self.assertIn("original meaning differs from native Bootstrap", result.stderr)
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)

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
                    for identifier in round_["cases"]:
                        case = inputs[identifier]
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
        state = self.state()
        self.assertEqual(len(state["encodings"]), 1)
        self.assertTrue(state["encodings"][0]["complete"])
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["nodes"]), 4)
        carried = next(n for n in state["nodes"] if n["original_ids"] == ["L00007"])
        self.assertEqual(carried["subject"], "Topic 6")
        self.assertIn("bootstrap", carried)

    def test_all_ready_families_share_one_native_batch_with_their_own_parents(self):
        from sse_multivector import hierarchy_generation as generation

        self.configure(count=84)
        self.automatic_runner()
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        with (
            patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log), FAKE_V3="1"),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["status"], "complete")
        state = self.state()
        groups = []
        for record in state["experiments"]:
            if record["role"] != "consolidation":
                continue
            inputs = [json.loads(v["INPUT_JSON"]) for v in record["inputs"].values()]
            parents = {
                json.dumps(v["parent"], sort_keys=True) for v in inputs if "parent" in v
            }
            groups.append(len(parents))
        self.assertGreaterEqual(
            max(groups),
            5,
            "all five ready families must be submitted together, not capped or split by family",
        )

    def test_bad_family_does_not_hold_healthy_families_in_a_shared_batch(self):
        from sse_multivector import hierarchy_generation as generation

        self.configure(count=56)
        self.automatic_runner()
        needle = 'os.environ["FAKE_RUNNER_PROMPT_RESPONSE"]=json.dumps(value)'
        code = """if "parent" in payload and os.environ.get("FAKE_BAD_PARENT"):
        marker=Path(os.environ["FAKE_BAD_PARENT"])
        with marker.open("a+") as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            stream.seek(0)
            title=stream.read()
            if not title:
                title=payload["parent"]["title"]
                stream.write(title)
            if title==payload["parent"]["title"]:
                value=None
    """
        self.runner.write_text(self.runner.read_text().replace(needle, code + needle))
        self.cli("prepare-hierarchy", "trial", "--spec", self.root / "hierarchy.json")
        marker = self.root / "bad-parent.txt"
        with (
            patch.dict(
                os.environ,
                FAKE_RUNNER_LOG=str(self.log),
                FAKE_V3="1",
                FAKE_BAD_PARENT=str(marker),
            ),
            patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=FixtureEncoder(),
            ),
        ):
            result = generation.run(self.root / "trial")
        self.assertEqual(result["execution_status"], "blocked")
        state = self.state()
        roots = [n for n in state["nodes"] if not n["parents"]]
        bad = next(n for n in roots if n["subject"] == marker.read_text())
        self.assertFalse(any(bad["id"] in n["parents"] for n in state["nodes"]))
        for root in roots:
            if root != bad:
                self.assertTrue(any(root["id"] in n["parents"] for n in state["nodes"]))
        self.assertTrue(
            any(
                not record.get("complete")
                and {answer["status"] for answer in record.get("answers", {}).values()}
                >= {"valid", "malformed"}
                for record in state["experiments"]
            )
        )
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
            [0.001],
        )
        self.assertEqual(events[-1]["event"], "recovered")
        timings = [json.loads(line) for line in
                   (self.root/'trial/advance-timings.jsonl').read_text().splitlines()]
        self.assertTrue(any(r['mode'] == 'subprocess-recovery' and r.get('initial_error') for r in timings))

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

    def test_viewer_reads_frozen_constructor_sources_without_allowing_advancement(self):
        from sse_multivector import hierarchy_generation as generation

        self.cli("prepare-hierarchy", "trial", "--spec", self.configure(count=3))
        self.bootstrap()
        self.encode_pending()
        state = self.state()
        frozen = self.root / "frozen-constructor/sse_multivector"
        frozen.mkdir(parents=True)
        for name in generation.CODE_FILES:
            old = str(PROJECT / "sse_multivector" / name)
            new = frozen / name
            new.write_bytes(Path(old).read_bytes())
            state["sources"][str(new)] = state["sources"].pop(old)
        self.write("trial/state.json", state)
        before = (self.root / "trial/state.json").read_bytes()
        calls = self.calls()

        self.cli("export-canonical-viewer", "trial", "--output", "view")
        view = json.loads((self.root / "view/hierarchy.json").read_text())
        self.assertEqual(len(view["notes"]), 3)
        rejected = self.cli("advance-hierarchy", "trial", "--comment", "wrong checkout", ok=False)
        self.assertIn("construction source binding changed", rejected.stderr)
        self.assertEqual((self.root / "trial/state.json").read_bytes(), before)

        missing = str(frozen / "worker.py")
        digest = state["sources"].pop(missing)
        self.write("trial/state.json", state)
        rejected = self.cli("export-canonical-viewer", "trial", "--output", "missing", ok=False)
        self.assertIn("invalid hierarchy construction source bindings", rejected.stderr)
        self.assertFalse((self.root / "missing").exists())
        state["sources"][missing] = digest
        (self.root / "trial/state.json").write_bytes(before)

        with (frozen / "worker.py").open("a") as stream:
            stream.write("\n# Changed frozen source\n")
        rejected = self.cli("export-canonical-viewer", "trial", "--output", "changed", ok=False)
        self.assertIn("hierarchy source changed", rejected.stderr)
        self.assertFalse((self.root / "changed").exists())
        self.assertEqual(self.calls(), calls)

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
