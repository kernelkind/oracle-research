"""Offline integration tests of the supported experiment CLI and real runner engine."""

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


CLI = Path(__file__).with_name("experiment.py")


class ExperimentTests(unittest.TestCase):
    def test_subject_context_nodes_select_every_direct_entry_and_reuse_saved_requests(self):
        self.prompt.write_text('GENERIC PROMPT CONTEXT PROMINENCE\n{INPUT_JSON}')
        posts = [dict(note_id='N1', text='☕ Tea warms me.', subjects=[dict(
            number=number, subject='Tea', context=context,
            byte_spans=[[4, 7]], fragments=['Tea']) for number, context in (
                ('1', 'Tea warms the writer.'), ('1.1', 'The writer mentions tea.'))]),
            dict(note_id='N2', text='Tea.', subjects=[dict(number='2', subject='Tea',
                context='The post names tea.', byte_spans=[[0, 3]], fragments=['Tea'])])]
        self.write('subjects.json', {'notes': posts})
        members = [dict(instance='V'+str(i), note_id=p['note_id'], text=p['text'],
                        byte_spans=p['subjects'][0]['byte_spans'], fragments=['Tea'])
                   for i, p in enumerate(posts, 1)]
        self.write('hierarchy.json', {'memberships': {'nodes': [dict(
            group='G', title='Tea', recursive_note_ids=['N1', 'N2', 'child'],
            matched_instances=members), dict(group='child', title='Tea ritual',
                matched_instances=[dict(instance='V3', note_id='N1', text=posts[0]['text'],
                                        byte_spans=[[8, 13]], fragments=['warms'])])]}})
        selector = dict(schema_version=1, subjects='subjects.json', hierarchy='hierarchy.json',
                        selections=[dict(id='original', node_id='G', note_id='N1', number='1')])
        self.write('selection.json', selector)
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_contexts', path='selection.json')
        self.write('spec.json', spec)
        self.prepare()
        answer = dict(missing_meaning='Some meaning is missing.', prominence=80,
                      allocation=[dict(meaning='Tea', points=100, represented=80, missing=20)])
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        del selector['selections']
        selector['nodes'] = ['G']
        self.write('selection.json', selector)
        self.prepare('E2')
        cases = self.show('E2')['cases']
        self.assertEqual({(c['evidence']['note_id'], c['evidence']['subject_number'])
                          for c in cases}, {('N1', '1'), ('N1', '1.1'), ('N2', '2')})
        self.assertTrue(all(c['evidence']['node_id'] == 'G' for c in cases))
        self.assertTrue(all(set(json.loads(c['inputs']['INPUT_JSON'])) == {'context', 'post'}
                            for c in cases))
        self.cli('run', 'E2', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        self.assertEqual(self.show('E2')['summary']['reused'], 1)
        self.assertEqual(len(self.calls()), 3)
        for nodes in (['missing'], ['G', 'G']):
            selector['nodes'] = nodes
            self.write('selection.json', selector)
            self.cli('prepare', 'bad', '--spec', self.spec, ok=False)
            self.assertFalse((self.root/'bad').exists())
        selector['nodes'] = ['G']
        self.write('selection.json', selector)
        posts[1]['subjects'] = []
        self.write('subjects.json', {'notes': posts})
        error = self.cli('prepare', 'missing-context', '--spec', self.spec, ok=False)
        self.assertIn('no saved SP context', error.stderr)

    def test_subject_contexts_freeze_source_text_and_validate_prominence(self):
        self.prompt.write_text('GENERIC PROMPT CONTEXT PROMINENCE\n{INPUT_JSON}')
        post = dict(note_id='N1', text='☕ Tea warms me.', subjects=[dict(
            number='1', subject='Tea', context='Tea warms the writer.',
            byte_spans=[[4, 7]], fragments=['Tea'])])
        self.write('subjects.json', {'notes': [post]})
        self.write('hierarchy.json', {'memberships': {'nodes': [dict(
            group='G', title='Tea', recursive_note_ids=['N1', 'child'],
            matched_instances=[dict(instance='V1', note_id='N1', text=post['text'],
                                    byte_spans=[[4, 7]], fragments=['Tea'])])]}})
        self.write('selection.json', dict(schema_version=1, subjects='subjects.json',
            hierarchy='hierarchy.json', selections=[dict(
                id='tea-context', node_id='G', note_id='N1', number='1')]))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_contexts', path='selection.json')
        self.write('spec.json', spec)
        self.prepare()
        case = self.show('E1', '--case', 'tea-context')
        self.assertEqual(json.loads(case['inputs']['INPUT_JSON']),
                         {'context': 'Tea warms the writer.', 'post': post['text']})
        self.assertEqual(case['evidence']['mask_ids'], ['V1'])
        self.assertEqual(case['evidence']['subject_number'], '1')
        sources = json.loads((self.root/'E1/experiment.json').read_text())['plan']['sources']
        self.assertTrue(all(str(self.root/name) in sources
                            for name in ('selection.json', 'subjects.json', 'hierarchy.json')))
        answer = dict(missing_meaning='The speaker is not identified.',
                      allocation=[dict(meaning='Warmth', points=100, represented=80, missing=20)],
                      prominence=80)
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        self.assertEqual(self.show('E1')['cases'][0]['status'], 'valid')
        self.prepare('E2')
        self.cli('run', 'E2')
        self.assertEqual(self.show('E2')['summary']['reused'], 1)
        self.assertEqual(len(self.calls()), 1)
        from sse_multivector import experiment_inputs
        answer['allocation'][0]['represented'] = 79
        with self.assertRaisesRegex(ValueError, 'allocation'):
            experiment_inputs.validate(spec['dataset'], case, json.dumps(answer), None)
        post['subjects'][0]['byte_spans'] = [[8, 13]]
        post['subjects'][0]['fragments'] = ['warms']
        self.write('subjects.json', {'notes': [post]})
        self.cli('prepare', 'outside', '--spec', self.spec, ok=False)
        self.assertFalse((self.root/'outside').exists())

    def test_combined_prominence_uses_direct_post_span_union_and_reuses_unchanged_requests(self):
        self.prominence_spec()
        masks = [dict(instance=mid, note_id='N1', text='☕ Tea, then tea.',
                      byte_spans=spans, fragments=fragments)
                 for mid, spans, fragments in (
                     ('V1', [[4, 7]], ['Tea']),
                     ('V2', [[4, 13]], ['Tea, then']),
                     ('V3', [[14, 17]], ['tea']))]
        masks.append(dict(instance='V4', note_id='N2', text='Tea.',
                          byte_spans=[[0, 3]], fragments=['Tea']))
        self.write('cases.json', {'memberships': {'nodes': [
            dict(group='G', title='Tea', matched_instances=masks,
                 recursive_note_ids=['N1', 'N2', 'N3']),
            dict(group='child', title='Tea ritual', matched_instances=[dict(
                instance='V5', note_id='N1', text='☕ Tea, then tea.',
                byte_spans=[[0, 18]], fragments=['☕ Tea, then tea.'])])]}})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['select'] = ['G']
        self.write('spec.json', spec)
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"prominence":80}'})
        self.assertEqual(len(self.calls()), 4)

        spec['dataset']['combine_masks'] = True
        self.write('spec.json', spec)
        self.prepare('E2')
        cases = self.show('E2')['cases']
        self.assertEqual(len(cases), 2)
        combined = next(c for c in cases if c['evidence']['note_id'] == 'N1')
        self.assertEqual(combined['evidence']['mask_ids'], ['V1', 'V2', 'V3'])
        self.assertEqual(combined['evidence']['byte_spans'], [[4, 13], [14, 17]])
        self.assertEqual(json.loads(combined['inputs']['INPUT_JSON']),
                         {'mask': ['Tea, then', 'tea'],
                          'marked_post': '☕ ⟦Tea, then⟧ ⟦tea⟧.'})
        self.cli('run', 'E2', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"prominence":80}'})
        report = self.show('E2')
        self.assertEqual(report['summary']['reused'], 1)
        self.assertEqual(len(self.calls()), 5)
        from sse_multivector import experiment, experiment_inputs
        batch, _ = experiment_inputs.review_batch(experiment.load(self.root/'E2')[0], report)
        self.assertEqual(len(batch['notes']), 2)

    def test_reuse_verification_does_not_reread_whole_files_per_case(self):
        from collections import Counter
        from unittest.mock import MagicMock, patch
        from sse_multivector import extraction_pipeline as engine

        self.write('cases.json', {'cases': [
            {'id': str(i), 'inputs': {'POST': str(i)}} for i in range(8)]})
        self.prepare()
        self.cli('run', 'E1')
        manifest_path = self.root/'E1/run/manifest.json'
        ledger_path = self.root/'E1/run/results.jsonl'
        manifest = json.loads(manifest_path.read_text())
        keys = [engine._prompt_request_key(manifest, p['text']) for p in manifest['prompts']]
        opens, scans = Counter(), Counter()
        original_open = Path.open
        def tracked_open(path, *args, **kwargs):
            opens[path] += 1
            stream = original_open(path, *args, **kwargs)
            proxy = MagicMock(wraps=stream)
            proxy.__enter__.return_value = proxy
            proxy.__exit__.side_effect = stream.__exit__
            def iterate():
                scans[path] += 1
                return iter(stream)
            proxy.__iter__.side_effect = iterate
            return proxy
        with patch.object(Path, 'open', tracked_open):
            history = engine.RequestHistory(self.root)
            for key in keys:
                reference, source = next(history.matches(key))
                self.assertEqual(source['request_sha256'], key)
        # One manifest parse/hash per operation; one receipt scan and direct
        # seeks for individual receipts, not repeated scans from byte zero.
        self.assertEqual(opens[manifest_path], 1)
        self.assertEqual(opens[ledger_path], 1 + len(keys))
        self.assertEqual(scans[ledger_path], 1)

    def test_warm_reuse_cache_rejects_changed_files_and_handles_append(self):
        from sse_multivector import extraction_pipeline as engine
        self.prepare()
        self.cli('run', 'E1')
        manifest_path = self.root/'E1/run/manifest.json'
        ledger_path = self.root/'E1/run/results.jsonl'
        manifest = json.loads(manifest_path.read_text())
        key = engine._prompt_request_key(manifest, manifest['prompts'][0]['text'])
        history = engine.RequestHistory(self.root)
        reference, source = next(history.matches(key))
        for path, old, new in [(manifest_path, b'fixture/model', b'changed/model'),
                                (ledger_path, b'Tea', b'Bad')]:
            with self.subTest(path=path):
                saved = path.read_bytes()
                stamp = path.stat()
                path.write_bytes(saved.replace(old, new))
                # Size and mtime alone must not make changed data look unchanged.
                os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                with self.assertRaises(engine.RunnerError):
                    next(history.matches(key))
                path.write_bytes(saved)
                self.assertEqual(next(history.matches(key))[1], source)
        saved = ledger_path.read_bytes()
        replacement = ledger_path.with_suffix('.replacement')
        replacement.write_bytes(saved.replace(b'Tea', b'Bad'))
        replacement.replace(ledger_path)
        with self.assertRaises(engine.RunnerError):
            next(history.matches(key))
        ledger_path.write_bytes(saved)
        line = saved.splitlines(keepends=True)[reference['result_line'] - 1]
        with ledger_path.open('ab') as stream:
            stream.write(line)
        appended = dict(reference, result_line=len(saved.splitlines()) + 1)
        self.assertEqual(engine._read_request_source(appended, key, files=history.files), source)
        # Inserting a line invalidates cached offsets; the old line number no
        # longer identifies the receipt, even though its bytes still exist.
        ledger_path.write_bytes(b'{}\n' + saved)
        with self.assertRaises(engine.RunnerError):
            next(history.matches(key))

    def test_shared_receipt_reads_are_safe_across_workers_and_report_operations(self):
        from concurrent.futures import ThreadPoolExecutor
        from unittest.mock import patch
        from sse_multivector import experiment, extraction_pipeline as engine
        self.prepare()
        self.cli('run', 'E1')
        self.cli('prepare', 'E2', '--from', 'E1')
        self.cli('run', 'E2')
        path = self.root/'E1/run/manifest.json'
        manifest = json.loads(path.read_text())
        keys = [engine._prompt_request_key(manifest, p['text']) for p in manifest['prompts']]
        history = engine.RequestHistory(self.root)
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda key: next(history.matches(key))[1]['request_sha256'], keys * 10))
        self.assertEqual(results, keys * 10)
        with patch.object(engine, '_sha256_file', wraps=engine._sha256_file) as hashed:
            self.assertEqual(experiment.report(self.root/'E2')['summary']['valid'], 2)
            self.assertNotIn(path, [call.args[0] for call in hashed.call_args_list])
        path.write_text(path.read_text().replace('fixture/model', 'changed/model'))
        self.assertEqual(experiment.report(self.root/'E2')['summary']['invalid_receipt'], 2)

    def test_warm_receipt_provenance_is_invalidated_by_a_changed_upgrade_ledger(self):
        from dataclasses import replace
        from sse_multivector import experiment, extraction_pipeline as engine
        self.prepare()
        self.cli('run', 'E1')
        self.cli('prepare', 'E2', '--from', 'E1')
        self.cli('run', 'E2')
        _, config, manifest = experiment.load(self.root/'E2')
        record = json.loads((self.root/'E2/run/results.jsonl').read_text().splitlines()[0])
        config = replace(config, prompts=(config.prompts[0],))
        files = engine.ReceiptFiles()
        engine.validate_prompt_receipt(config, manifest, record, files=files)
        self.write('E2/run/runner-upgrades.jsonl', {'invalid': 'upgrade'})
        with self.assertRaises(engine.RunnerError):
            engine.validate_prompt_receipt(config, manifest, record, files=files)

    def test_prominence_hierarchy_with_explicit_diagnostic_schema(self):
        self.prominence_spec()
        self.write('cases.json', {'memberships': {'nodes': [dict(
            group='G', title='Tea', matched_instances=[dict(instance='V1', note_id='N1',
            text='Tea.', byte_spans=[[0, 3]], fragments=['Tea'])])]}})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['select'] = ['G']
        spec['runner']['output_schema'] = {
            'type': 'object', 'required': ['prominence', 'allocation'],
            'properties': {'prominence': {'type': 'integer'}, 'allocation': {'type': 'array'}},
            'additionalProperties': False}
        self.write('spec.json', spec)
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                 '{"prominence":80,"allocation":[]}'})
        case = self.show('E1', '--case', 'G-V1')
        self.assertEqual(case['status'], 'valid')
        self.assertEqual(case['parsed'], {'prominence': 80, 'allocation': []})
        self.assertEqual(case['evidence']['mask_ids'], ['V1'])
        self.assertEqual(json.loads(case['inputs']['INPUT_JSON']),
                         {'mask': ['Tea'], 'marked_post': '⟦Tea⟧.'})

    def test_completed_review_and_intentional_repeat_do_not_scan_request_history(self):
        from unittest.mock import patch
        from sse_multivector import experiment

        self.prominence_spec()
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"prominence":80}'})
        viewer = self.root / 'viewer'
        viewer.write_text('#!/usr/bin/env python3\n')
        viewer.chmod(0o755)
        # Exercise the actual CLI review handler, including its report on exit.
        args = experiment.parser().parse_args([
            'review', str(self.root / 'E1'), '--ui', '--ui-binary', str(viewer)])
        with patch.object(experiment.engine, 'RequestHistory',
                          side_effect=AssertionError('unnecessary history scan')):
            experiment.review(args)
            result = experiment.report(self.root / 'E1')
        self.assertEqual(result['requests']['unrun'], 0)

        self.cli('prepare', 'repeat', '--from', 'E1', '--repeat')
        with patch.object(experiment.engine, 'RequestHistory',
                          side_effect=AssertionError('repeat must not search reuse')):
            result = experiment.report(self.root / 'repeat')
        self.assertEqual(result['requests']['new'], 2)
        self.assertEqual(result['requests']['reusable'], 0)

    def test_title_review_selection_preserves_assessments_without_inference(self):
        self.prompt.write_text("GENERIC PROMPT\n{NUMBERED_INSTANCES}")
        self.cases.write_text(json.dumps({"packets": [
            {"packet": key, "instances": [{"instance": key, "vector_id": key,
                "note_id": key, "text": text, "byte_spans": [[0, len(text)]],
                "fragments": [text]}]}
            for key, text in [("T1", "Tea"), ("T2", "Coffee"), ("T3", "Milk")]
        ]}))
        spec = json.loads(self.spec.read_text())
        spec["dataset"]["adapter"] = "titles"
        self.spec.write_text(json.dumps(spec))
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"title":"Tea"}'})
        for key, verdict in [("T1", "reject"), ("T2", "uncertain"), ("T3", "accept")]:
            self.cli("review", "E1", "--case", key, "--role", "agent",
                     "--verdict", verdict, "--comment", "Scope assessment for " + key)
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
            "Path(__file__).with_suffix('.json').write_text(json.dumps({"
            "'args':sys.argv[1:], 'batch':json.loads(Path(sys.argv[2]).read_text())}))\n"
        )
        viewer.chmod(0o755)
        before = self.calls()
        self.cli("review", "E1", "--ui", "--only", "T1", "--ui-binary", viewer)
        selected = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual(selected["args"][0], "review-titles")
        self.assertEqual(len(selected["args"]), 3)
        self.assertEqual([x["item_id"] for x in selected["batch"]["items"]], ["T1"])
        self.assertIn("Scope assessment for T1", selected["batch"]["items"][0]["assessment"])
        binding = json.loads((self.root / "E1/review-ui.json").read_text())[0]
        self.assertEqual(list(binding["cases"]), ["T1"])
        self.cli("review", "E1", "--ui", "--flagged-only", "--ui-binary", viewer)
        flagged = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual([x["item_id"] for x in flagged["batch"]["items"]], ["T1", "T2"])
        self.cli("review", "E1", "--ui", "--ui-binary", viewer)
        full = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual(len(full["batch"]["items"]), 3)
        no_match = self.cli("review", "E1", "--ui", "--only", "T3", "--flagged-only",
                            "--ui-binary", self.root / "missing-binary")
        self.assertIn("No flagged cases", no_match.stdout)
        error = self.cli("review", "E1", "--ui", "--only", "missing", ok=False)
        self.assertIn("unknown --only", error.stderr)
        self.assertEqual(self.calls(), before)

    def test_filtered_title_review_opens_existing_ui_and_preserves_decisions(self):
        self.test_titles_dedup_masks_and_keep_full_posts_out_of_model_input()
        self.open_existing_ui_and_approve("--only", "T1")
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.show("E1", "--case", "T1")["reviews"][-1]["verdict"], "accept")

    def test_prepare_subset_preserves_exact_inputs_baseline_and_reuse(self):
        self.prepare()
        self.cli("run", "E1")
        original = self.show()["cases"][1]
        self.cli("prepare", "E2", "--from", "E1", "--only", "two")
        subset = self.show("E2")["cases"]
        self.assertEqual([c["id"] for c in subset], ["two"])
        self.assertEqual(subset[0]["prompt"], original["prompt"])
        self.assertEqual(subset[0]["inputs"], original["inputs"])
        self.assertEqual(subset[0]["baseline"]["output"], original["output"])
        self.cli("run", "E2")
        self.assertEqual(len(self.calls()), 2)
        self.cli("prepare", "E3", "--from", "E1", "--only", "two",
                 "--model", "fixture/other", "--reasoning-effort", "low")
        self.cli("run", "E3")
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.calls()[-1]["prompt"], original["prompt"])
        self.assertEqual(self.calls()[-1]["request"]["model"], "fixture/other")
        plan = json.loads((self.root / "E3" / "experiment.json").read_text())["plan"]
        self.assertEqual([c["id"] for c in plan["baseline"]["cases"]], ["two"])
        error = self.cli("prepare", "bad", "--from", "E1", "--only", "unknown", ok=False)
        self.assertIn("unknown --only", error.stderr)
        self.assertFalse((self.root / "bad").exists())

    def test_explicit_prominence_selection_keeps_missing_results_without_judgments(self):
        self.prominence_spec()
        self.prepare()
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
            "Path(__file__).with_suffix('.json').write_text(Path(sys.argv[1]).read_text())\n"
        )
        viewer.chmod(0o755)
        self.cli("review", "E1", "--ui", "--only", "tea-second", "--ui-binary", viewer)
        batch = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual([n["id"] for n in batch["notes"]], ["tea-second"])
        self.assertIn("unrun", batch["notes"][0]["title"])
        self.assertFalse((self.root / "E1" / "reviews.jsonl").exists())
        self.cli("review", "E1", "--ui", "--only", "tea-second", "--only", "tea-first",
                 "--flagged-only", "--ui-binary", viewer)
        batch = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual([n["id"] for n in batch["notes"]], ["tea-first", "tea-second"])
        for args in [("--ui", "--only", "missing"), ("--only", "tea-first")]:
            error = self.cli("review", "E1", *args, ok=False)
            self.assertIn("--only", error.stderr)
        self.assertEqual(self.calls(), [])

    def test_flagged_mask_review_keeps_empty_results_and_full_session_batch(self):
        self.mask_spec()
        self.prepare()
        response = json.dumps(
            {"meaning": "Tea", "expressible": False, "evidence": "none", "mask": []}
        )
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": response})
        cases = self.show()["cases"]
        self.cli("review", "E1", "--case", cases[0]["id"], "--role", "agent",
                 "--verdict", "reject", "--comment", "Tea is directly selectable.")
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
            "Path(__file__).with_suffix('.json').write_text(json.dumps({"
            "'args':sys.argv[1:], 'batch':json.loads(Path(sys.argv[2]).read_text())}))\n"
        )
        viewer.chmod(0o755)
        before = self.calls()
        self.cli("review", "E1", "--ui", "--flagged-only", "--ui-binary", viewer)
        flagged = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual(flagged["args"][3:], ["--only", cases[0]["id"]])
        self.assertEqual(len(flagged["batch"]["items"]), 2)
        item = flagged["batch"]["items"][0]
        self.assertEqual(item["fragments"], [])
        self.assertEqual(item["result_status"], "empty")
        self.assertEqual(item["note"], cases[0]["inputs"]["POST"])
        self.assertIn("Tea is directly selectable", item["assessment"])
        self.cli("review", "E1", "--ui", "--ui-binary", viewer)
        full = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual(full["args"][:3], flagged["args"][:3])
        self.cli("review", "E1", "--ui", "--only", cases[0]["id"], "--ui-binary", viewer)
        explicit = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual(explicit, flagged)
        no_match = self.cli("review", "E1", "--ui", "--only", cases[1]["id"],
                            "--flagged-only", "--ui-binary", self.root / "missing-binary")
        self.assertIn("No flagged cases", no_match.stdout)
        self.assertEqual(self.calls(), before)
        self.assertEqual(self.show()["cases"][0]["reviews"][-1]["role"], "agent")

    def test_flagged_selection_uses_current_reviews_and_user_decisions(self):
        from sse_multivector import experiment_inputs as inputs

        def case(status="valid", reviews=()):
            return dict(status=status, reviews=reviews)

        def review(role, verdict, current=True):
            return dict(role=role, verdict=verdict, current=current)

        self.assertFalse(inputs.is_flagged(case()))
        self.assertFalse(inputs.is_flagged(case("empty")))
        for status in ("failed", "unrun", "malformed", "invalid_receipt"):
            self.assertTrue(inputs.is_flagged(case(status)))
        self.assertTrue(inputs.is_flagged(case("empty", [review("agent", "reject")])))
        self.assertFalse(inputs.is_flagged(case(reviews=[review("agent", "reject", False)])))
        self.assertFalse(inputs.is_flagged(case(reviews=[review("agent", "reject"), review("agent", "accept")])))
        self.assertFalse(inputs.is_flagged(case("failed", [review("user", "accept"), review("agent", "reject")])))
        self.assertTrue(inputs.is_flagged(case(reviews=[review("user", "uncertain")])))

    def test_flagged_prominence_review_keeps_unscored_and_no_match_is_safe(self):
        self.prominence_spec()
        self.prepare()
        self.cli("run", "E1", "--max-new-attempts", "1",
                 env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"prominence":80}'}, ok=False)
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
            "Path(__file__).with_suffix('.json').write_text(Path(sys.argv[1]).read_text())\n"
        )
        viewer.chmod(0o755)
        before = self.calls()
        self.cli("review", "E1", "--ui", "--flagged-only", "--ui-binary", viewer)
        batch = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual([n["id"] for n in batch["notes"]], ["tea-second"])
        self.assertIn("unrun", batch["notes"][0]["title"])
        self.assertIn("No output", batch["notes"][0]["results"][0]["output"])
        self.cli("review", "E1", "--case", "tea-second", "--role", "user",
                 "--verdict", "accept", "--comment", "Acknowledged missing score")
        result = self.cli("review", "E1", "--ui", "--flagged-only", "--ui-binary", self.root / "missing-binary")
        self.assertIn("No flagged cases", result.stdout)
        self.assertFalse((self.root / "E1" / "review-ui.json").exists())
        self.assertEqual(self.calls(), before)
        error = self.cli("review", "E1", "--flagged-only", ok=False)
        self.assertIn("requires --ui", error.stderr)

    def test_mask_review_includes_failed_and_unrun_without_fabricating_spans(self):
        from sse_multivector import experiment_inputs as inputs

        self.mask_spec()
        self.prepare()
        result = self.show()
        result["cases"][0].update(status="malformed", output="broken JSON", error="invalid JSON")
        plan = json.loads((self.root / "E1" / "experiment.json").read_text())["plan"]
        batch, excluded = inputs.review_batch(plan, result)
        self.assertEqual(excluded, [])
        self.assertEqual([i["result_status"] for i in batch["items"]], ["malformed", "unrun"])
        self.assertTrue(all(i["fragments"] == [] for i in batch["items"]))
        self.assertIn("broken JSON", batch["items"][0]["details"])
        self.assertIn("invalid JSON", batch["items"][0]["details"])

    def test_thinking_on_survives_prepare_run_and_receipts(self):
        self.prepare()
        self.cli(
            "prepare", "thinking", "--from", "E1", "--provider", "openrouter",
            "--model", "xiaomi/mimo-v2.6-flash", "--reasoning-effort", "on",
        )
        self.assertEqual(self.show("thinking")["settings"]["reasoning_effort"], "on")
        self.cli("run", "thinking")
        for call in self.calls():
            self.assertEqual(call["request"]["reasoning"], "on")
            self.assertEqual(call["request"]["model"], "xiaomi/mimo-v2.6-flash")
        self.assertEqual(self.show("thinking")["summary"]["valid"], 2)

    def prominence_spec(self):
        self.prompt.write_text("GENERIC PROMPT {INPUT_JSON}")
        self.write(
            "cases.json",
            {
                "cases": [
                    {
                        "id": "tea-first",
                        "node_id": "tea",
                        "node_title": "Tea",
                        "note_id": "N1",
                        "text": "☕ Tea, then tea.",
                        "mask_ids": ["V1"],
                        "byte_spans": [[4, 7]],
                    },
                    {
                        "id": "tea-second",
                        "node_id": "tea",
                        "node_title": "Tea",
                        "note_id": "N1",
                        "text": "☕ Tea, then tea.",
                        "mask_ids": ["V2", "V3"],
                        "byte_spans": [[14, 17]],
                    },
                ]
            },
        )
        value = json.loads(self.spec.read_text())
        value["dataset"]["adapter"] = "prominence"
        self.spec.write_text(json.dumps(value))

    def test_prominence_ui_shows_each_full_post_mask_and_unrun_case_without_calls(self):
        self.prominence_spec()
        self.prepare()
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport json, sys\nfrom pathlib import Path\n"
            "assert len(sys.argv) == 4 and sys.argv[2] == '--comments', sys.argv\n"
            "batch = json.loads(Path(sys.argv[1]).read_text())\n"
            "Path(__file__).with_suffix('.json').write_text(json.dumps(batch))\n"
        )
        viewer.chmod(0o755)
        self.cli("review", "E1", "--ui", "--ui-binary", viewer)
        batch = json.loads(viewer.with_suffix(".json").read_text())
        self.assertEqual(
            [n["text"] for n in batch["notes"]],
            ["☕ ⟦Tea⟧, then tea.", "☕ Tea, then ⟦tea⟧."],
        )
        self.assertTrue(all("unrun" in n["title"] for n in batch["notes"]))
        self.assertIn("V2, V3", batch["notes"][1]["title"])
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.root / "E1" / "review-ui.json").exists())
        self.assertEqual(self.show("E1", "--case", "tea-first")["reviews"], [])
        binary = CLI.parents[1] / "target/release/model-output-review"
        if binary.is_file():
            check = subprocess.run(
                [str(binary), str(viewer.with_suffix(".json")), "--check"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(check.returncode, 0, check.stderr)

    def test_prominence_ui_comments_persist_without_becoming_decisions(self):
        self.prominence_spec()
        self.prepare()
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport json, sys, hashlib\nfrom pathlib import Path\n"
            "assert sys.argv[2] == '--comments'\n"
            "batch = json.loads(Path(sys.argv[1]).read_text())\n"
            "note = batch['notes'][0]; result = note['results'][0]\n"
            "session = {'comments': {result['comment_key']: {'note_id': note['id'], "
            "'model': result['model'], 'comment': 'Too high — 日本語'}}}\n"
            "raw = json.dumps(session, ensure_ascii=False, separators=(',', ':')).encode()\n"
            "Path(sys.argv[3]).write_text(json.dumps({'schema_version': 1, "
            "'state_sha256': hashlib.sha256(raw).hexdigest(), 'session': session}))\n"
        )
        viewer.chmod(0o755)
        self.cli("review", "E1", "--ui", "--only", "tea-first", "--ui-binary", viewer)
        case = self.show("E1", "--case", "tea-first")
        review = case["reviews"][-1]
        self.assertEqual(review["comment"], "Too high — 日本語")
        self.assertEqual(review["verdict"], "comment")
        self.assertEqual(review["role"], "user")
        self.assertTrue(review["current"])
        self.assertEqual(self.show("E1", "--case", "tea-second")["reviews"], [])
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"prominence":80}'})
        stale = self.show("E1", "--case", "tea-first")["reviews"][-1]
        self.assertFalse(stale["current"])
        from sse_multivector import experiment_inputs as inputs
        self.assertTrue(inputs.is_flagged({"status": "valid", "reviews": [
            {"role": "agent", "verdict": "uncertain", "current": True}, review]}))

    def test_prominence_comments_round_trip_through_real_ui(self):
        import fcntl
        import pty
        import select
        import signal
        import struct
        import termios
        import time

        binary = CLI.parents[1] / "target/release/model-output-review"
        if not binary.is_file():
            self.skipTest("model-output-review binary unavailable")
        self.prominence_spec()
        self.prepare()
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
        process = subprocess.Popen(
            [sys.executable, str(CLI), "review", str(self.root / "E1"),
             "--ui", "--only", "tea-first"], stdin=slave, stdout=slave, stderr=slave,
            env={**os.environ, "TERM": "xterm"}, start_new_session=True)
        os.close(slave)
        captured, sent = b"", False
        try:
            deadline = time.monotonic() + 15
            while process.poll() is None and time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        captured += os.read(master, 65536)
                    except OSError:
                        break
                    if not sent and b"Add/edit" in captured:
                        os.write(master, b"cNeeds review\rq")
                        sent = True
            process.wait(timeout=2)
            self.assertEqual(process.returncode, 0, captured.decode(errors="replace"))
            self.assertTrue(sent)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            os.close(master)
        case = self.show("E1", "--case", "tea-first")
        self.assertEqual(case["reviews"][-1]["comment"], "Needs review")
        self.assertEqual(case["reviews"][-1]["verdict"], "comment")
        self.assertTrue(case["reviews"][-1]["current"])
        self.assertEqual(self.show("E1", "--case", "tea-second")["reviews"], [])
        self.assertEqual(self.calls(), [])

    def test_prominence_validates_scores_and_never_sends_node_metadata(self):
        self.prominence_spec()
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"prominence":0}'})
        case = self.show("E1", "--case", "tea-first")
        self.assertEqual(case["parsed"], {"prominence": 0})
        self.assertEqual(case["status"], "valid")
        for call in self.calls():
            payload = json.loads(call["prompt"].removeprefix("GENERIC PROMPT "))
            self.assertEqual(set(payload), {"mask", "marked_post"})
        from sse_multivector import experiment_inputs as inputs

        for raw in [
            '{"prominence":true}',
            '{"prominence":1.5}',
            '{"prominence":101}',
            '{"prominence":-1}',
            '{"prominence":5,"extra":1}',
            '{"prominence":1,"prominence":2}',
            "broken",
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                inputs.validate({"adapter": "prominence"}, case, raw, None)

    def test_cosine_review_uses_saved_results_without_calls_or_decisions(self):
        self.prominence_spec()
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"prominence":80}'})
        before = self.calls()
        rows = []
        for case in self.show("E1")["cases"]:
            evidence = case["evidence"]
            rows.append(dict(id=case["id"], node_id="tea", title="Tea", note_id="N1",
                             mask_ids=evidence["mask_ids"], prominence=80,
                             fragments=[evidence["text"].encode()[a:b].decode()
                                        for a, b in evidence["byte_spans"]],
                             cosine=.1 if case["id"] == "tea-first" else .9))
        self.write("cosines.json", {"groups": {"tea": rows}})
        viewer = self.root / "viewer"
        viewer.write_text(
            "#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n"
            "data=json.loads(Path(sys.argv[1]).read_text())\n"
            "assert len(data['orderings'])==2\n"
            "assert data['orderings'][1]['name']=='Linear cosine'\n"
            "assert data['orderings'][0]['note_ids']==['tea-first','tea-second']\n"
            "assert data['orderings'][1]['note_ids']==['tea-second','tea-first']\n"
        )
        viewer.chmod(0o755)
        self.cli("review", "E1", "--ui", "--ui-binary", viewer,
                 "--cosine-comparison", "cosines.json")
        self.assertEqual(self.calls(), before)
        self.assertFalse((self.root / "E1" / "reviews.jsonl").exists())
        self.assertFalse((self.root / "E1" / "review-ui.json").exists())

    def test_generic_prominence_view_selects_node_and_starts_in_combined_order(self):
        from sse_multivector.experiment_inputs import prepare_prominence
        self.prominence_spec()
        source = json.loads(self.cases.read_text())
        extra = dict(source['cases'][0], id='other', node_id='other', node_title='Other')
        source['cases'].append(extra)
        self.write('cases.json', {'cases': prepare_prominence(source)})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['adapter'] = 'generic'
        spec['runner']['output_schema'] = {'type': 'object', 'required': ['prominence']}
        self.write('spec.json', spec)
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                 '{"prominence":80,"allocation":[],"missing_meaning":"test"}'})
        rows = []
        for case in self.show()['cases']:
            if case['evidence']['node_id'] != 'tea':
                continue
            e = case['evidence']
            rows.append(dict(id=case['id'], node_id='tea', title='Tea', note_id='N1',
                             mask_ids=e['mask_ids'], prominence=80,
                             fragments=json.loads(case['inputs']['INPUT_JSON'])['mask'],
                             cosine=.1 if case['id']=='tea-first' else .9))
        self.write('cosines.json', {'groups': {'tea': rows}})
        viewer = self.root/'viewer'
        viewer.write_text(
            '#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\n'
            "Path(__file__).with_suffix('.json').write_text(json.dumps({"
            "'args':sys.argv[2:], 'batch':json.loads(Path(sys.argv[1]).read_text())}))\n")
        viewer.chmod(0o755)
        before = self.calls()
        options = ('--ui','--view','prominence','--node','tea','--cosine-comparison',
                   'cosines.json','--ordering','Linear cosine','--ui-binary',viewer)
        self.cli('review','E1',*options,'--check')
        shown = json.loads(viewer.with_suffix('.json').read_text())
        self.assertIn('--check', shown['args'])
        self.assertNotIn('--comments', shown['args'])
        batch = shown['batch']
        self.assertEqual(batch['orderings'][0]['name'], 'Linear cosine')
        self.assertEqual(batch['orderings'][0]['note_ids'], ['tea-second','tea-first'])
        self.assertEqual({n['id'] for n in batch['notes']}, {'tea-first','tea-second'})
        self.assertEqual(batch['notes'][0]['text'], '☕ ⟦Tea⟧, then tea.')
        self.cli('review','E1',*options)
        shown = json.loads(viewer.with_suffix('.json').read_text())
        self.assertIn('--comments', shown['args'])
        viewer.write_text(viewer.read_text() +
            "\nimport hashlib\n"
            "batch=json.loads(Path(sys.argv[1]).read_text()); n=batch['notes'][0]; r=n['results'][0]\n"
            "session={'comments':{r['comment_key']:{'note_id':n['id'],'model':r['model'],'comment':'Review this'}}}\n"
            "raw=json.dumps(session,ensure_ascii=False,separators=(',',':')).encode()\n"
            "Path(sys.argv[3]).write_text(json.dumps({'schema_version':1,'state_sha256':hashlib.sha256(raw).hexdigest(),'session':session}))\n")
        self.cli('review','E1',*options)
        comment = self.show('E1','--case','tea-first')['reviews'][-1]
        self.assertEqual((comment['verdict'],comment['comment'],comment['current']),
                         ('comment','Review this',True))
        self.assertEqual(self.calls(), before)
        self.assertFalse((self.root/'E1/reviews.jsonl').exists())
        for extra_args, error in [(('--node','absent'),'unknown --node'),
                                  (('--ordering','missing'),'unknown ordering')]:
            bad = self.cli('review','E1',*options,*extra_args,ok=False)
            self.assertIn(error,bad.stderr)
        # A generic input cannot impersonate a mask review using unrelated evidence.
        data = json.loads(self.cases.read_text())
        data['cases'][0]['inputs']['INPUT_JSON'] = '{"mask":["wrong"],"marked_post":"wrong"}'
        self.write('cases.json', data)
        self.prepare('E2')
        bad = self.cli('review','E2','--ui','--view','prominence','--node','tea',
                       '--ui-binary',viewer,ok=False)
        self.assertIn('input',bad.stderr)

    def test_prominence_review_sorts_within_nodes_without_omitting_failures(self):
        from sse_multivector import experiment_inputs as inputs

        self.prominence_spec()
        self.prepare()
        rows = self.show()["cases"]
        low, high = rows
        low.update(
            status="valid", output='{"prominence":10}', parsed={"prominence": 10}
        )
        high.update(
            status="valid", output='{"prominence":90}', parsed={"prominence": 90}
        )
        import copy

        other = copy.deepcopy(low)
        other.update(id="other")
        other["evidence"].update(node_id="other", node_title="Other node")
        failed = copy.deepcopy(low)
        failed.update(
            id="failed", status="failed", output=None, error="provider failure"
        )
        malformed = copy.deepcopy(low)
        malformed.update(
            id="malformed", status="malformed", output="not json", error="invalid JSON"
        )
        plan = json.loads((self.root / "E1" / "experiment.json").read_text())["plan"]
        batch, excluded = inputs.review_batch(
            plan, {"cases": [low, other, failed, high, malformed]}
        )
        self.assertEqual(excluded, [])
        self.assertEqual(
            [n["id"] for n in batch["notes"]],
            [high["id"], low["id"], "failed", "malformed", "other"],
        )
        self.assertIn("score 90", batch["notes"][0]["title"])
        self.assertEqual(batch["notes"][0]["results"][0]["output"], "Prominence: 90 / 100")
        self.assertEqual(high["output"], '{"prominence":90}')
        self.assertIn("unranked", batch["notes"][2]["title"])
        self.assertIn("provider failure", batch["notes"][2]["results"][0]["comment"])
        self.assertEqual(batch["notes"][3]["results"][0]["output"], "not json")
        high["parsed"]["prominence"] = 10
        tied, _ = inputs.review_batch(plan, {"cases": [high, low]})
        self.assertEqual(
            [n["id"] for n in tied["notes"]], sorted([high["id"], low["id"]])
        )

    def test_prominence_input_keeps_fragments_together_and_rejects_invalid_offsets(
        self,
    ):
        from sse_multivector import experiment_inputs as inputs

        self.prominence_spec()
        source = json.loads(self.cases.read_text())
        source["cases"] = source["cases"][:1]
        item = source["cases"][0]
        item["byte_spans"] = [[4, 7], [14, 17]]
        prepared = inputs.prepare({"adapter": "prominence"}, source, "{INPUT_JSON}")
        payload = json.loads(prepared[0]["inputs"]["INPUT_JSON"])
        self.assertEqual(
            payload, {"mask": ["Tea", "tea"], "marked_post": "☕ ⟦Tea⟧, then ⟦tea⟧."}
        )
        for spans in [
            [],
            [[0, 1]],
            [[4, 99]],
            [[4, 7], [6, 8]],
            [[14, 17], [4, 7]],
            [[True, 3]],
        ]:
            item["byte_spans"] = spans
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                inputs.prepare({"adapter": "prominence"}, source, "{INPUT_JSON}")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runner = self.root / "runner"
        self.runner.write_text(FAKE_RUNNER)
        self.runner.chmod(0o755)
        self.log = self.root / "calls.json"
        self.prompt = self.root / "v1.txt"
        self.prompt.write_text('GENERIC PROMPT {POST}\n{"literal_json":true}\n')
        self.cases = self.write(
            "cases.json",
            {
                "cases": [
                    {
                        "id": "one",
                        "inputs": {"POST": "Tea {POST}"},
                        "evidence": {"private": "REVIEW ONLY"},
                    },
                    {"id": "two", "inputs": {"POST": "Coffee"}},
                ]
            },
        )
        self.spec = self.write(
            "spec.json",
            {
                "schema_version": 1,
                "prompt": {"id": "P1", "path": "v1.txt"},
                "dataset": {"adapter": "generic", "path": "cases.json"},
                "runner": {
                    "runner_binary": str(self.runner),
                    "auth_file": None,
                    "provider": "openai-codex",
                    "model": "fixture/model",
                    "reasoning_effort": "low",
                    "concurrency": 1,
                },
            },
        )

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return path

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run(
            [sys.executable, str(CLI), *map(str, args)],
            cwd=self.root,
            env={**os.environ, "FAKE_RUNNER_LOG": str(self.log), **(env or {})},
            text=True,
            capture_output=True,
            timeout=30,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def prepare(self, name="E1", *args):
        return self.cli("prepare", name, "--spec", self.spec, *args)

    def show(self, name="E1", *args):
        return json.loads(self.cli("show", name, *args, "--json").stdout)

    def calls(self):
        return json.loads(self.log.read_text()) if self.log.exists() else []

    def test_prepare_is_offline_freezes_inputs_and_separates_review_evidence(self):
        result = self.prepare()
        self.assertIn("Model calls made: 0", result.stdout)
        self.assertEqual(self.calls(), [])
        case = self.show("E1", "--case", "one")
        self.assertIn("Tea {POST}", case["prompt"])
        self.assertNotIn("REVIEW ONLY", case["prompt"])
        self.assertEqual(case["evidence"]["private"], "REVIEW ONLY")
        self.assertEqual(case["status"], "unrun")
        self.prompt.write_text("Changed source after prepare")
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 2)
        self.assertTrue(
            all(c["prompt"].startswith("GENERIC PROMPT") for c in self.calls())
        )

    def subject_pairs_spec(self):
        self.prompt.write_text('GENERIC PROMPT\n{INPUT_JSON}')
        (self.root / 'selection').mkdir()
        subjects = [
            dict(index=i, subject=name, context=context, note_id=post,
                 note_short_id=post, number=str(i + 1), mask_vector_ids=[],
                 fragments=[], byte_spans=[])
            for i, (name, context, post) in enumerate([
                ('Tea', 'A cup of tea.', 'N1'),
                ('Tea', 'A cup of tea.', 'N2'),
                ('Drinks', 'Tea bags supply a drink.', 'N3'),
                ('Teas', 'Several teas.', 'N2'),
                ('Tea', 'Another reference to tea.', 'N1'),
                ('Tea bags', 'Bags for tea.', 'N1'),
                ('Tea bags', 'Tea in bags.', 'N3'),
            ])]
        subjects[0].update(mask_vector_ids=['saved-vector'], fragments=['Tea'], byte_spans=[[0, 3]])
        self.write('subjects.json', dict(subjects=subjects,
            posts=[dict(note_id=p, note_short_id=p, text='Tea. REVIEW ONLY ' + p)
                   for p in ['N1', 'N2', 'N3']], edges=[[0, 5], [2, 6]]))
        self.write('hierarchy.json', dict(groups=[[2], [0, 1, 3, 4], [5, 6]],
            member_to_group=[1, 1, 0, 1, 1, 2, 2], edges=[[0, 2], [1, 2]]))
        self.write('selection/pairs.json', dict(schema_version=1,
            inputs='../subjects.json', hierarchy='../hierarchy.json', pairs=[
                dict(id='pair', A='S0000', B='S0002'),
                dict(id='reverse', A='S0002', B='S0000')]))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='selection/pairs.json')
        self.write('spec.json', spec)

    def test_subject_pairs_prepare_from_saved_nodes_without_copying_case_data(self):
        self.subject_pairs_spec()
        result = self.prepare()
        self.assertIn('Model calls made: 0', result.stdout)
        self.assertEqual(self.calls(), [])
        case = self.show('E1', '--case', 'pair')
        payload = {'A': [
            {'subject': 'Tea', 'context': 'A cup of tea.'},
            {'subject': 'Teas', 'context': 'Several teas.'},
            {'subject': 'Tea', 'context': 'Another reference to tea.'}],
            'B': [{'subject': 'Drinks', 'context': 'Tea bags supply a drink.'}]}
        self.assertEqual(case['inputs'], {'INPUT_JSON': json.dumps(payload, ensure_ascii=False, indent=2)})
        self.assertNotIn('REVIEW ONLY', case['prompt'])
        self.assertNotIn('S0000', case['prompt'])
        self.assertNotIn('saved-vector', case['prompt'])
        evidence = case['evidence']
        self.assertEqual(evidence['A']['node_id'], 'S0000')
        self.assertEqual(evidence['A']['group_index'], 1)
        self.assertEqual([e['index'] for e in evidence['A']['subject_entries']], [0, 1, 3, 4])
        self.assertEqual(evidence['A']['subject_entries'][0]['mask_vector_ids'], ['saved-vector'])
        self.assertEqual(evidence['A']['subject_entries'][0]['byte_spans'], [[0, 3]])
        self.assertEqual(len(evidence['source_posts']), 3)
        self.assertEqual(evidence['shared_children'], [dict(
            id='S0005', names=['Tea bags'], a_posts=['N1'], b_posts=['N3'])])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        for name in ['subjects.json', 'hierarchy.json', 'selection/pairs.json']:
            path = self.root / name
            self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        # A saved experiment remains self-contained if the source files change.
        self.write('subjects.json', {})
        self.assertEqual(self.show('E1', '--case', 'pair')['inputs'], case['inputs'])
        self.assertEqual(self.calls(), [])

    def test_subject_pairs_selection_preserves_orientation(self):
        self.subject_pairs_spec()
        spec = json.loads(self.spec.read_text())
        spec['dataset']['select'] = ['reverse']
        self.write('spec.json', spec)
        self.prepare()
        report = self.show()
        self.assertEqual([c['id'] for c in report['cases']], ['reverse'])
        payload = json.loads(report['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(payload['A'][0]['subject'], 'Drinks')
        self.assertEqual(payload['B'][0]['subject'], 'Tea')
        shared = report['cases'][0]['evidence']['shared_children'][0]
        self.assertEqual(shared['a_posts'], ['N3'])
        self.assertEqual(shared['b_posts'], ['N1'])
        self.assertEqual(self.calls(), [])

    def test_subject_pairs_reuse_generic_saved_answers_without_another_call(self):
        self.subject_pairs_spec()
        self.prepare()
        cases = self.show()['cases']
        generic = [{'id': c['id'], 'inputs': c['inputs']} for c in cases]
        self.write('cases.json', {'cases': generic})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='generic', path='cases.json')
        self.write('spec.json', spec)
        self.prepare('baseline')
        self.cli('run', 'baseline')
        self.assertEqual(len(self.calls()), 2)
        # Reuse binds the exact request, not the input adapter or review evidence.
        self.assertEqual(self.show()['requests']['reusable'], 2)
        self.cli('run', 'E1')
        self.assertEqual(self.show()['summary']['reused'], 2)
        self.assertEqual(len(self.calls()), 2)

    def test_subject_pairs_reject_invalid_sources_and_selections_before_preparing(self):
        self.subject_pairs_spec()
        names = ['subjects.json', 'hierarchy.json', 'selection/pairs.json', 'spec.json']
        originals = {name: (self.root / name).read_text() for name in names}
        checks = [
            ('selection/pairs.json', lambda x: x['pairs'][0].update(A='S9999'), 'unknown hierarchy node'),
            ('selection/pairs.json', lambda x: x['pairs'][0].update(A='S0002'), 'distinct hierarchy nodes'),
            ('selection/pairs.json', lambda x: x['pairs'][1].update(id='pair'), 'duplicate case identity'),
            ('selection/pairs.json', lambda x: x.update(schema_version=True), 'schema_version'),
            ('selection/pairs.json', lambda x: x.update(inputs='missing.json'), 'missing.json'),
            ('spec.json', lambda x: x['dataset'].update(select=['missing']), 'unknown case requested'),
            ('spec.json', lambda x: x['dataset'].update(select=['pair', 'pair']), 'duplicate selection'),
            ('hierarchy.json', lambda x: x['groups'][1].append(2), 'repeated hierarchy subject'),
            ('hierarchy.json', lambda x: x['groups'][0].__setitem__(0, -1), 'invalid or repeated'),
            ('hierarchy.json', lambda x: x['groups'][0].__setitem__(0, True), 'invalid or repeated'),
            ('hierarchy.json', lambda x: x['groups'][0].clear(), 'group must be nonempty'),
            ('hierarchy.json', lambda x: x['groups'][1].remove(4), 'do not cover'),
            ('hierarchy.json', lambda x: x['member_to_group'].__setitem__(0, 0), 'mapping differs'),
            ('hierarchy.json', lambda x: x['edges'].append([0, 99]), 'invalid hierarchy or SP edge'),
            ('subjects.json', lambda x: x['subjects'][0].update(index=9), 'index does not match'),
            ('subjects.json', lambda x: x['subjects'][0].update(context=None), 'context must be a string'),
            ('subjects.json', lambda x: x['subjects'][0].update(note_id='missing'), 'unknown source post'),
            ('subjects.json', lambda x: x['posts'].append(x['posts'][0]), 'duplicate source post'),
            ('subjects.json', lambda x: x['edges'].append([0, 99]), 'invalid hierarchy or SP edge'),
        ]
        for name, change, error in checks:
            with self.subTest(source=name, error=error):
                for source, contents in originals.items():
                    (self.root / source).write_text(contents)
                data = json.loads(originals[name])
                change(data)
                self.write(name, data)
                result = self.cli('prepare', 'bad', '--spec', self.spec, ok=False)
                self.assertIn(error, result.stderr)
                self.assertFalse((self.root / 'bad').exists())
                self.assertEqual(self.calls(), [])

    def test_inherit_baseline_resume_and_repeat_are_distinct(self):
        self.prepare()
        self.cli("run", "E1")
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 2)
        self.cli("prepare", "E2", "--from", "E1")
        self.assertEqual(self.show("E2")["requests"]["reusable"], 2)
        self.cli("run", "E2")
        report = self.show("E2")
        self.assertEqual(report["summary"]["reused"], 2)
        self.assertEqual(report["usage"]["input_tokens"], 0)
        self.assertEqual(report["comparison"]["unchanged"], 2)
        self.cli("prepare", "E3", "--from", "E1", "--repeat")
        self.cli("run", "E3")
        self.assertEqual(len(self.calls()), 4)
        self.cli("run", "E3")
        self.assertEqual(len(self.calls()), 4)

    def test_changed_prompt_uses_saved_baseline_and_reports_no_quality_verdict(self):
        self.prepare()
        self.cli("run", "E1")
        next_prompt = self.root / "v2.txt"
        next_prompt.write_text("GENERIC PROMPT revised {POST}")
        self.cli(
            "prepare",
            "E2",
            "--from",
            "E1",
            "--prompt",
            next_prompt,
            "--prompt-id",
            "P2",
        )
        self.cli("run", "E2")
        self.assertEqual(len(self.calls()), 4)
        report = self.show("E2")
        self.assertEqual(report["comparison"]["changed"], 2)
        self.assertNotIn("improvement", report)
        self.assertEqual(
            self.show("E2", "--case", "one")["baseline"]["status"], "valid"
        )

    def test_prepared_artifact_tampering_refuses_to_send(self):
        self.prepare()
        config = self.root / "E1" / "runner-config.json"
        value = json.loads(config.read_text())
        value["model"] = "other/model"
        config.write_text(json.dumps(value))
        result = self.cli("run", "E1", ok=False)
        self.assertIn("changed", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_local_failure_does_not_block_others_or_retry_on_resume(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_FAILURES": json.dumps({
            "Tea": {"metadata": {"abort_reason": {"name": "TimeoutError"}}}
        })})
        report = self.show()
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["valid"], 1)
        self.assertEqual(report["cases"][0]["failure_kind"], "local")
        self.cli("run", "E1", ok=False)
        self.assertEqual(len(self.calls()), 2)

    def test_provider_timeout_retries_once_and_preserves_both_receipts(self):
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_FAILURES": json.dumps({
            "Tea": {"attempts": 1, "metadata": {"http_status": 200,
                "error": {"code": 504, "message": "Upstream idle timeout exceeded"}}}
        })})
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.show()["summary"]["valid"], 2)
        records = [json.loads(line) for line in (self.root / "E1/run/results.jsonl").read_text().splitlines()]
        self.assertEqual([r["status"] for r in records if r["note_id"] == "one"], ["failed", "succeeded"])
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 3)

    def test_provider_retry_limit_survives_resume(self):
        self.prepare()
        failure = {"FAKE_RUNNER_FAILURES": json.dumps({"Tea": {"metadata": {"http_status": 503}}})}
        self.cli("run", "E1", ok=False, env=failure)
        self.assertEqual(len(self.calls()), 3)
        self.cli("run", "E1", ok=False)
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.show()["summary"]["valid"], 1)

    def test_codex_processing_error_retries_only_missing_case_on_resume(self):
        self.prepare()
        message = ("Codex error: An error occurred while processing your request. "
                   "You can retry your request, or contact us through our help center "
                   "at help.openai.com if the error persists.")
        self.cli("run", "E1", "--max-new-attempts", "2", ok=False, env={
            "FAKE_RUNNER_FAILURES": json.dumps({"Tea": {
                "error": message, "metadata": {"http_status": 200}}})})
        before = (self.root / "E1/run/results.jsonl").read_bytes()
        self.assertEqual(self.show()["summary"]["valid"], 1)
        self.cli("run", "E1", "--max-new-attempts", "1")
        self.assertEqual(self.show()["summary"]["valid"], 2)
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.calls()[-1]["prompt"].splitlines()[0], "GENERIC PROMPT Tea {POST}")
        self.assertTrue((self.root / "E1/run/results.jsonl").read_bytes().startswith(before))
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 3)

    def test_codex_processing_error_classification_preserves_retry_guards(self):
        from copy import deepcopy
        from sse_multivector.extraction_pipeline import prompt_failure_kind, provider_retry_delay

        record = {"exit_code": 1, "attempt": 1, "model_result": {
            "provider": "openai-codex", "stop_reason": "error",
            "error": "Codex error: An error occurred while processing your request. You can retry your request, or contact us",
            "response_metadata": {"http_status": 200}}}
        self.assertEqual(prompt_failure_kind(record), "provider_transient")
        self.assertEqual(provider_retry_delay(record), 2.0)
        for changes, metadata, outer, expected in [
            ({"provider": "openrouter"}, {}, {}, "unknown"),
            ({"stop_reason": "stop"}, {}, {}, "unknown"),
            ({"error": "You can retry your request"}, {}, {}, "unknown"),
            ({"error": "Codex error: An error occurred while processing your request."}, {}, {}, "unknown"),
            ({"error": {"message": "You can retry your request"}}, {}, {}, "unknown"),
            ({}, {"http_status": 400}, {}, "unknown"),
            ({}, {"error": {"code": "unsupported_parameter"}}, {}, "unknown"),
            ({}, {"http_status": 401}, {}, "provider_fatal"),
            ({}, {"abort_reason": {"name": "TimeoutError"}}, {}, "local"),
            ({}, {}, {"exit_code": 0}, "local"),
            ({}, {}, {"exit_code": None}, "local"),
            ({}, {}, {"attempt": 2}, "provider_transient"),
            ({}, {"retry_after": "120"}, {}, "provider_transient"),
        ]:
            with self.subTest(changes=changes, metadata=metadata, outer=outer):
                candidate = deepcopy(record)
                candidate.update(outer)
                candidate["model_result"].update(changes)
                candidate["model_result"]["response_metadata"].update(metadata)
                self.assertEqual(prompt_failure_kind(candidate), expected)
                self.assertIsNone(provider_retry_delay(candidate))

    def test_due_retries_precede_untouched_cases_in_deadline_order(self):
        self.write("cases.json", {"cases": [
            {"id": text, "inputs": {"POST": text}}
            for text in ["Tea", "Coffee", "Milk", "Water"]
        ]})
        self.prepare()
        self.cli("run", "E1", env={
            "FAKE_RUNNER_FAILURES": json.dumps({
                text: {"attempts": 1, "metadata": {"http_status": 503}}
                for text in ["Tea", "Coffee"]
            }),
            "FAKE_RUNNER_SEQUENCE": json.dumps({"Milk": {"sleep_seconds": 2.1}}),
        })
        self.assertEqual([c["prompt"].splitlines()[0] for c in self.calls()],
                         ["GENERIC PROMPT " + text for text in
                          ["Tea", "Coffee", "Milk", "Tea", "Coffee", "Water"]])
        self.assertEqual(self.show()["summary"]["valid"], 4)

    def test_resumed_retry_precedes_untouched_cases_when_due(self):
        self.write("cases.json", {"cases": [
            {"id": text, "inputs": {"POST": text}}
            for text in ["Tea", "Coffee", "Milk"]
        ]})
        self.prepare()
        self.cli("run", "E1", "--max-new-attempts", "1", ok=False, env={
            "FAKE_RUNNER_FAILURES": json.dumps({
                "Tea": {"attempts": 1, "metadata": {"http_status": 503}}
            }),
        })
        before = (self.root / "E1/run/results.jsonl").read_bytes()
        self.cli("run", "E1", env={
            "FAKE_RUNNER_SEQUENCE": json.dumps({"Coffee": {"sleep_seconds": 2.1}}),
        })
        self.assertEqual([c["prompt"].splitlines()[0] for c in self.calls()],
                         ["GENERIC PROMPT " + text for text in
                          ["Tea", "Coffee", "Tea", "Milk"]])
        self.assertTrue((self.root / "E1/run/results.jsonl").read_bytes().startswith(before))
        self.assertEqual(self.show()["summary"]["valid"], 3)

    def test_unknown_failure_is_not_retried(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_FAIL_STAGE": "prompt"})
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(self.show()["summary"]["failed"], 2)

    def test_malformed_provider_metadata_is_unknown_and_does_not_block_other_cases(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_FAILURES": json.dumps({
            "Tea": {"metadata": ["not an error object"]}
        })})
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(self.show()["cases"][0]["failure_kind"], "unknown")

    def test_shared_auth_error_stops_later_cases(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_FAILURES": json.dumps({
            "Tea": {"metadata": {"http_status": 401}}
        })})
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.show()["summary"]["unrun"], 1)

    def test_explicit_new_attempt_allowance_bounds_calls(self):
        self.prepare()
        self.cli("run", "E1", "--max-new-attempts", "1", ok=False)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.show()["summary"]["unrun"], 1)
        self.cli("run", "E1", "--max-new-attempts", "1")
        self.assertEqual(len(self.calls()), 2)

    def test_slow_case_does_not_block_later_independent_case(self):
        spec = json.loads(self.spec.read_text())
        spec["runner"]["concurrency"] = 2
        self.write("spec.json", spec)
        data = json.loads(self.cases.read_text())
        data["cases"].append({"id": "three", "inputs": {"POST": "Third"}})
        self.write("cases.json", data)
        self.prepare()
        marker = str(self.root / "third-started")
        self.cli("run", "E1", env={"FAKE_RUNNER_SEQUENCE": json.dumps({
            "Tea": {"wait_for": marker}, "Third": {"touch": marker}
        })})
        self.assertEqual(self.show()["summary"]["valid"], 3)

    def test_local_abort_overrides_provider_error_and_unknown_transport_not_retried(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_FAILURES": json.dumps({
            "Tea": {"metadata": {"http_status": 503, "abort_reason": {"name": "TimeoutError"}}},
            "Coffee": {"metadata": {"http_status": 200, "transport_error": {"message": "connection lost"}}}
        })})
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual([c["failure_kind"] for c in self.show()["cases"]], ["local", "unknown"])

    def test_execution_upgrade_is_explicit_preserves_results_and_is_audited(self):
        self.prepare()
        self.cli("run", "E1", "--max-new-attempts", "1", ok=False)
        before = (self.root / "E1/run/results.jsonl").read_bytes()
        envelope = json.loads((self.root / "E1/experiment.json").read_text())
        envelope["plan"]["code"]["experiment.py"] = "0" * 64
        envelope["sha256"] = hashlib.sha256((json.dumps(envelope["plan"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
        self.write("E1/experiment.json", envelope)
        self.cli("run", "E1", ok=False)
        self.assertEqual(len(self.calls()), 1)
        self.cli("run", "E1", "--runner-upgrade-reason", "Approved failure handling update")
        self.assertEqual(len(self.calls()), 2)
        self.assertTrue((self.root / "E1/run/results.jsonl").read_bytes().startswith(before))
        self.assertTrue((self.root / "E1/code-upgrades.jsonl").exists())
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 2)

    def test_engine_upgrade_records_new_receipt_provenance(self):
        data = json.loads(self.cases.read_text())
        data["cases"][1]["inputs"] = data["cases"][0]["inputs"]
        self.write("cases.json", data)
        self.prepare()
        manifest = json.loads((self.root / "E1/run/manifest.json").read_text())
        manifest["wrapper_sha256"] = "0" * 64
        (self.root / "E1/run/manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        envelope = json.loads((self.root / "E1/experiment.json").read_text())
        def digest(value):
            return hashlib.sha256((json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
        envelope["plan"]["manifest_sha256"] = digest(manifest)
        envelope["plan"]["code"]["extraction_pipeline.py"] = "0" * 64
        envelope["sha256"] = digest(envelope["plan"])
        self.write("E1/experiment.json", envelope)
        self.cli("run", "E1", "--runner-upgrade-reason", "Approved executor upgrade")
        self.assertEqual(self.show()["summary"]["valid"], 2)
        self.assertEqual(self.show()["summary"]["reused"], 1)
        self.assertTrue((self.root / "E1/run/runner-upgrades.jsonl").exists())
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 1)

    def test_long_retry_after_is_not_ignored(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_FAILURES": json.dumps({
            "Tea": {"metadata": {"http_status": 429, "retry_after": "120"}}
        })})
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(self.show()["summary"]["valid"], 1)

    def test_validation_failure_never_retries_even_with_provider_error_metadata(self):
        self.prepare()
        self.cli("run", "E1", ok=False, env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "valid": False, "response_metadata": {"http_status": 503}
        })})
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual([c["failure_kind"] for c in self.show()["cases"]], ["local", "local"])

    def test_resume_retries_provider_case_but_not_local_case(self):
        data = json.loads(self.cases.read_text())
        data["cases"].append({"id": "three", "inputs": {"POST": "Third"}})
        self.write("cases.json", data)
        self.prepare()
        self.cli("run", "E1", "--max-new-attempts", "2", ok=False,
                 env={"FAKE_RUNNER_FAILURES": json.dumps({
                     "Tea": {"metadata": {"http_status": 504}},
                     "Coffee": {"metadata": {"abort_reason": {"name": "TimeoutError"}}}
                 })})
        self.assertEqual(len(self.calls()), 2)
        self.cli("run", "E1", ok=False)
        self.assertEqual(len(self.calls()), 4)
        self.assertEqual(self.show()["summary"]["valid"], 2)
        self.assertEqual(self.show()["cases"][1]["failure_kind"], "local")

    def test_same_id_different_inputs_cannot_be_paired_with_baseline(self):
        self.prepare()
        self.cli("run", "E1")
        data = json.loads(self.cases.read_text())
        data["cases"][0]["inputs"]["POST"] = "Changed actual input"
        self.cases.write_text(json.dumps(data))
        self.prepare("E2", "--baseline", "E1")
        report = self.show("E2")
        self.assertEqual(report["comparison"]["input_mismatch"], 1)
        self.assertIsNone(self.show("E2", "--case", "one")["baseline"])
        self.assertEqual(len(self.calls()), 2)

    def test_reviews_keep_assessments_and_user_decisions_separate(self):
        self.prepare()
        self.cli(
            "review",
            "E1",
            "--case",
            "one",
            "--role",
            "agent",
            "--verdict",
            "uncertain",
            "--comment",
            "Needs human review",
        )
        self.cli(
            "review",
            "E1",
            "--case",
            "one",
            "--role",
            "user",
            "--verdict",
            "accept",
            "--comment",
            "Explicit user decision",
        )
        case = self.show("E1", "--case", "one")
        self.assertEqual([x["role"] for x in case["reviews"]], ["agent", "user"])
        self.assertEqual(case["status"], "unrun")
        self.assertEqual(self.calls(), [])

    def mask_spec(self):
        self.prompt.write_text("GENERIC PROMPT\n{POST}\n{SUBJECT}\n{INDEXED_POST}")
        self.cases.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [
                        {
                            "note_id": "N1",
                            "text": "Tea helps. Tea helps.",
                            "subjects": [
                                {"subject": "Tea", "context": "REVIEW ONLY"},
                                {"subject": "Tea drinking"},
                            ],
                        },
                    ],
                }
            )
        )
        value = json.loads(self.spec.read_text())
        value["dataset"]["adapter"] = "masks"
        self.spec.write_text(json.dumps(value))

    def test_masks_expand_subjects_decode_positions_and_keep_empty_visible(self):
        self.mask_spec()
        result = self.prepare()
        self.assertIn("Posts: 1; subjects/calls: 2", result.stdout)
        response = json.dumps(
            {"meaning": "Tea", "expressible": False, "evidence": "none", "mask": []}
        )
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": response})
        report = self.show()
        self.assertEqual(report["summary"]["empty"], 2)
        self.assertEqual(len(report["cases"]), 2)
        self.assertTrue(
            all("REVIEW ONLY" not in call["prompt"] for call in self.calls())
        )
        case_id = report["cases"][0]["id"]
        data = json.loads(self.cases.read_text())
        data["notes"][0]["subjects"].reverse()
        self.cases.write_text(json.dumps(data))
        self.prepare("E2", "--baseline", "E1")
        self.assertEqual(self.show("E2")["cases"][1]["id"], case_id)

    def test_bad_mask_is_malformed_and_is_not_repaired_or_retried(self):
        self.mask_spec()
        self.prepare()
        self.cli(
            "run", "E1", ok=False, env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"mask": []}'}
        )
        self.assertEqual(self.show()["summary"]["malformed"], 2)
        self.cli("run", "E1", ok=False)
        self.assertEqual(len(self.calls()), 2)
        self.assertFalse((self.root / "E1/reviews.jsonl").exists())

    def test_titles_dedup_masks_and_keep_full_posts_out_of_model_input(self):
        self.prompt.write_text("GENERIC PROMPT\n{NUMBERED_INSTANCES}")
        instance = {
            "instance": "V1",
            "vector_id": "v1",
            "note_id": "N1",
            "text": "Tea PRIVATE POST CONTEXT",
            "byte_spans": [[0, 3]],
            "fragments": ["Tea"],
        }
        self.cases.write_text(
            json.dumps(
                {
                    "packets": [
                        {
                            "packet": "T1",
                            "instances": [
                                instance,
                                {**instance, "instance": "V2", "vector_id": "v2"},
                            ],
                        }
                    ]
                }
            )
        )
        value = json.loads(self.spec.read_text())
        value["dataset"]["adapter"] = "titles"
        self.spec.write_text(json.dumps(value))
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"title":"Tea"}'})
        case = self.show("E1", "--case", "T1")
        self.assertEqual(case["parsed"]["title"], "Tea")
        self.assertNotIn("PRIVATE", self.calls()[0]["prompt"])
        self.assertEqual(case["evidence"]["duplicates_removed"], 1)

    def test_json_schema_order_and_settings_are_preserved(self):
        value = json.loads(self.spec.read_text())
        schema = {
            "type": "object",
            "properties": {"z": {"type": "string"}, "a": {"type": "string"}},
            "required": ["z", "a"],
            "additionalProperties": False,
        }
        value["runner"]["output_schema"] = schema
        self.spec.write_text(json.dumps(value))
        self.prepare()
        self.cli(
            "run",
            "E1",
            env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"z":"first","a":"second"}'},
        )
        self.assertEqual(
            list(self.calls()[0]["request"]["schema"]["properties"]), ["z", "a"]
        )
        self.cli(
            "prepare",
            "E2",
            "--from",
            "E1",
            "--model",
            "fixture/other",
            "--reasoning-effort",
            "high",
        )
        self.assertEqual(self.show("E2")["requests"]["new"], 2)

    def test_import_verifies_rendered_inputs_and_does_not_rerun_old_batch(self):
        self.prepare()
        self.cli("run", "E1")
        config = self.root / "E1/runner-config.json"
        self.prepare("imported", "--import-config", config)
        self.assertEqual(self.show("imported")["summary"]["valid"], 2)
        self.cli("run", "imported", ok=False)
        self.cli("prepare", "candidate", "--from", "imported")
        self.cli("run", "candidate")
        self.assertEqual(self.show("candidate")["comparison"]["unchanged"], 2)
        self.assertEqual(len(self.calls()), 2)
        self.prompt.write_text("GENERIC PROMPT WRONG {POST}")
        result = self.cli(
            "prepare",
            "bad-import",
            "--spec",
            self.spec,
            "--import-config",
            config,
            ok=False,
        )
        self.assertIn("mapping", result.stderr)
        self.assertFalse((self.root / "bad-import").exists())

    def test_import_maps_legacy_ids_but_candidate_uses_stable_case_ids(self):
        self.prepare()
        self.cli("run", "E1")
        value = json.loads(self.cases.read_text())
        for case in value["cases"]:
            case["id"] = "stable-" + case["id"]
        self.cases.write_text(json.dumps(value))
        self.prepare("imported", "--import-config", self.root / "E1/runner-config.json")
        self.cli("prepare", "E2", "--from", "imported")
        self.cli("run", "E2")
        self.assertEqual(self.show("E2")["summary"]["valid"], 2)
        self.assertEqual(len(self.calls()), 2)

    def test_inherited_history_root_is_not_silently_changed(self):
        self.prepare()
        self.cli("run", "E1")
        (self.root / "elsewhere").mkdir()
        self.cli("prepare", "elsewhere/E2", "--from", "E1")
        self.assertEqual(self.show("elsewhere/E2")["requests"]["reusable"], 2)

    def test_active_run_lock_blocks_execution_but_not_show(self):
        import fcntl

        self.prepare()
        with (self.root / "E1/.experiment.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.cli("run", "E1", ok=False)
            self.assertIn("already active", result.stderr)
            self.assertEqual(self.show()["summary"]["unrun"], 2)
        self.assertEqual(self.calls(), [])

    def test_generic_selection_does_not_silently_run_unselected_cases(self):
        value = json.loads(self.spec.read_text())
        value["dataset"]["select"] = ["two"]
        self.spec.write_text(json.dumps(value))
        self.prepare()
        self.assertEqual(self.show()["summary"]["cases"], 1)
        self.cli("run", "E1")
        self.assertEqual(len(self.calls()), 1)

    def test_show_includes_exact_settings_without_opening_artifact_files(self):
        self.prepare()
        self.assertEqual(self.show()["settings"]["model"], "fixture/model")
        self.assertEqual(
            self.show("E1", "--case", "one")["settings"]["reasoning_effort"], "low"
        )

    def test_title_review_opens_the_existing_ui_without_inference(self):
        self.test_titles_dedup_masks_and_keep_full_posts_out_of_model_input()
        self.open_existing_ui_and_approve()
        self.assertEqual(len(self.calls()), 1)
        decisions = self.show("E1", "--case", "T1")["reviews"]
        self.assertEqual(decisions[-1]["role"], "user")
        self.assertEqual(decisions[-1]["verdict"], "accept")

    def test_mask_review_opens_the_existing_ui_and_preserves_decisions(self):
        self.mask_spec()
        self.prepare()
        response = json.dumps(
            {"meaning": "Tea", "expressible": True, "evidence": "Tea", "mask": [[1, 1]]}
        )
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": response})
        self.open_existing_ui_and_approve()
        self.assertEqual(len(self.calls()), 2)
        for case in self.show()["cases"]:
            self.assertEqual(case["reviews"][-1]["verdict"], "accept")

    def test_flagged_empty_mask_ui_records_only_selected_decision(self):
        self.mask_spec()
        self.prepare()
        response = json.dumps(
            {"meaning": "Tea", "expressible": False, "evidence": "none", "mask": []}
        )
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": response})
        cases = self.show()["cases"]
        self.cli("review", "E1", "--case", cases[0]["id"], "--role", "agent",
                 "--verdict", "uncertain", "--comment", "Review the empty answer.")
        self.open_existing_ui_and_approve("--flagged-only")
        cases = self.show()["cases"]
        self.assertEqual(cases[0]["reviews"][-1]["role"], "user")
        self.assertEqual(cases[0]["reviews"][-1]["verdict"], "accept")
        self.assertEqual(cases[1]["reviews"], [])
        self.assertEqual(len(self.calls()), 2)

    def open_existing_ui_and_approve(self, *options):
        import fcntl
        import pty
        import select
        import signal
        import struct
        import termios
        import time

        binary = CLI.parents[1] / "target/release/sse-mask-review"
        if not binary.is_file():
            self.skipTest("existing review UI binary unavailable")
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 100, 0, 0))
        process = subprocess.Popen(
            [sys.executable, str(CLI), "review", str(self.root / "E1"), "--ui", *options],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env={**os.environ, "TERM": "xterm"},
            start_new_session=True,
        )
        os.close(slave)
        captured = b""
        try:
            deadline = time.monotonic() + 8
            while process.poll() is None and time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        captured += os.read(master, 65536)
                    except OSError:
                        break
                    if b"Tea" in captured:
                        os.write(master, b"a\r")
            process.wait(timeout=2)
            self.assertEqual(process.returncode, 0, captured.decode(errors="replace"))
            self.assertEqual(len(list((self.root / "E1").glob("ui-*-session.json"))), 1)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            os.close(master)

    def test_rejects_missing_variables_unknown_settings_and_overwrite_without_calls(
        self,
    ):
        self.prompt.write_text("{POST} {MISSING}")
        self.cli("prepare", "E1", "--spec", self.spec, ok=False)
        self.assertFalse((self.root / "E1").exists())
        self.prompt.write_text("GENERIC PROMPT {POST}")
        self.prepare()
        self.cli("prepare", "E1", "--spec", self.spec, ok=False)
        value = json.loads(self.spec.read_text())
        value["runner"]["temprature"] = 1
        self.spec.write_text(json.dumps(value))
        self.cli("prepare", "E2", "--spec", self.spec, ok=False)
        self.assertEqual(self.calls(), [])

    def test_old_public_batch_commands_are_retired(self):
        pipeline = CLI.with_name("extraction_pipeline.py")
        result = subprocess.run(
            [sys.executable, str(pipeline), "--help"], capture_output=True, text=True
        )
        self.assertNotIn("revise-prompt", result.stdout)
        self.assertNotIn("{revise-prompt,masks", result.stdout)
        result = subprocess.run(
            [sys.executable, str(pipeline), "prompt", "old-config.json"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("experiment.py", result.stderr)
        help_result = subprocess.run(
            [sys.executable, str(pipeline), "prompt", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertNotIn("--repeat", help_result.stdout)

    def test_invalid_title_is_not_reused_in_a_new_experiment(self):
        self.test_titles_dedup_masks_and_keep_full_posts_out_of_model_input()
        self.cli("prepare", "bad", "--from", "E1", "--repeat")
        self.cli(
            "run", "bad", ok=False, env={"FAKE_RUNNER_PROMPT_RESPONSE": "not json"}
        )
        # Use a history root containing only the invalid run, not E1's valid answer.
        self.cli(
            "prepare", "next", "--from", "bad", "--history-root", self.root / "bad"
        )
        self.assertEqual(self.show("next")["requests"]["new"], 1)
        self.cli("run", "next", env={"FAKE_RUNNER_PROMPT_RESPONSE": '{"title":"Tea"}'})
        self.assertEqual(len(self.calls()), 3)

    def test_review_of_unrun_case_is_marked_stale_after_output_exists(self):
        self.prepare()
        self.cli(
            "review",
            "E1",
            "--case",
            "one",
            "--role",
            "agent",
            "--verdict",
            "uncertain",
            "--comment",
            "Input review only",
        )
        self.cli("run", "E1")
        self.assertFalse(self.show("E1", "--case", "one")["reviews"][0]["current"])

    def test_absent_cost_estimate_is_not_reported_as_zero_cost(self):
        self.prepare()
        self.cli("run", "E1")
        self.assertIsNone(self.show()["usage"]["catalog_cost_estimate_usd"])
        self.assertEqual(self.show()["usage"]["attempts_without_cost_estimate"], 2)

    def test_provider_cost_is_reported_separately_from_catalog_estimate(self):
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_RESULT_OVERRIDE": json.dumps({
            "response_metadata": {"usage": {"cost": 0.0001}}
        })})
        usage = self.show()["usage"]
        self.assertAlmostEqual(usage["provider_reported_cost_usd"], 0.0002)
        self.assertEqual(usage["attempts_without_provider_cost"], 0)
        self.assertIsNone(usage["catalog_cost_estimate_usd"])

    def test_cost_lookup_preserves_receipts_and_releases_reserve_on_resume(self):
        from unittest.mock import patch
        from sse_multivector import experiment
        spec = json.loads(self.spec.read_text())
        spec['runner']['provider'] = 'openrouter'
        self.spec.write_text(json.dumps(spec))
        self.prepare()
        self.cli('run', 'E1', '--max-cost-usd', '0.6', '--max-request-cost-usd', '0.4',
                 ok=False, env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
                     'response_metadata': {'id': 'gen-test'}})})
        receipts = self.root / 'E1/run/results.jsonl'
        before = receipts.read_bytes()
        reply = subprocess.CompletedProcess([], 0, json.dumps([
            {'id': 'gen-test', 'total_cost': 0, 'model': 'fixture/model'}]), '')
        with patch.object(experiment.subprocess, 'run', return_value=reply) as lookup:
            experiment.reconcile_costs(self.root / 'E1')
            lookup.assert_called_once()
        self.assertEqual(receipts.read_bytes(), before)
        self.assertEqual(self.show()['usage']['provider_reported_cost_usd'], 0)
        self.assertEqual(self.show()['usage']['attempts_without_provider_cost'], 0)
        with patch.object(experiment.subprocess, 'run') as lookup:
            experiment.reconcile_costs(self.root / 'E1')
            lookup.assert_not_called()
        self.cli('run', 'E1', '--max-cost-usd', '0.6', '--max-request-cost-usd', '0.4',
                 env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
                     'response_metadata': {'usage': {'cost': 0.1}}})})
        self.assertEqual(len(self.calls()), 2)
        self.assertTrue(receipts.read_bytes().startswith(before))
        self.assertEqual(self.show()['summary']['valid'], 2)
        self.assertAlmostEqual(self.show()['usage']['provider_reported_cost_usd'], 0.1)
        path = self.root / 'E1/run/cost-receipts.jsonl'
        receipt = json.loads(path.read_text())
        receipt['generation']['id'] = 'gen-unrelated'
        path.write_text(json.dumps(receipt) + '\n')
        with self.assertRaisesRegex(Exception, 'cost receipt'):
            experiment.report(self.root / 'E1')

    def test_cost_lookup_rejects_invalid_charge_without_releasing_reserve(self):
        from unittest.mock import patch
        from sse_multivector import experiment
        spec = json.loads(self.spec.read_text())
        spec['runner']['provider'] = 'openrouter'
        self.spec.write_text(json.dumps(spec))
        self.prepare('E1', '--only', 'one')
        self.cli('run', 'E1', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'response_metadata': {'id': 'gen-test'}})})
        for value in [-1, None, True, float('nan')]:
            with self.subTest(value=value), patch.object(experiment.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 0, json.dumps([
                        {'id': 'gen-test', 'total_cost': value, 'model': 'fixture/model'}]), '')):
                with self.assertRaisesRegex(ValueError, 'cost'):
                    experiment.reconcile_costs(self.root / 'E1')
        self.assertEqual(self.show()['usage']['attempts_without_provider_cost'], 1)
        with patch.object(experiment.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, json.dumps([{'id': 'gen-test', 'error': 'HTTP 404'}]), '')):
            experiment.reconcile_costs(self.root / 'E1')
        self.assertEqual(self.show()['usage']['attempts_without_provider_cost'], 1)

    def test_dollar_budget_preserves_uncapped_responses_and_counts_prior_spend(self):
        spec=json.loads(self.spec.read_text())
        spec['runner']['provider']='openrouter'
        self.spec.write_text(json.dumps(spec))
        self.prepare()
        env={'FAKE_RUNNER_RESULT_OVERRIDE':json.dumps({'response_metadata':{'usage':{'cost':0.4}}})}
        self.cli('run','E1','--max-cost-usd','0.6','--max-request-cost-usd','0.4',ok=False,env=env)
        self.assertEqual(len(self.calls()),1)
        self.assertNotIn('max_output_tokens',self.calls()[0]['request'])
        self.cli('run','E1','--max-cost-usd','0.6','--max-request-cost-usd','0.4',ok=False,env=env)
        self.assertEqual(len(self.calls()),1)
        self.cli('run','E1','--max-cost-usd','0.8','--max-request-cost-usd','0.4',env=env)
        self.assertEqual(len(self.calls()),2)

    def test_dollar_budget_waits_and_retains_unknown_billing_on_resume(self):
        spec=json.loads(self.spec.read_text())
        spec['runner'].update(provider='openrouter',concurrency=2)
        self.spec.write_text(json.dumps(spec))
        self.prepare()
        env={'FAKE_RUNNER_RESULT_OVERRIDE':json.dumps({'response_metadata':{'usage':{'cost':0.1}}})}
        self.cli('run','E1','--max-cost-usd','0.6','--max-request-cost-usd','0.4',env=env)
        self.assertEqual(len(self.calls()),2)
        self.prepare('E2','--repeat')
        self.cli('run','E2','--max-cost-usd','0.6','--max-request-cost-usd','0.4',ok=False)
        self.assertEqual(len(self.calls()),3)
        self.cli('run','E2','--max-cost-usd','0.45','--max-request-cost-usd','0.1',ok=False)
        self.assertEqual(len(self.calls()),3)
        self.cli('run','E2','--max-cost-usd','0.5','--max-request-cost-usd','0.1')
        self.assertEqual(len(self.calls()),4)
        self.assertEqual(self.show('E2')['summary']['valid'],2)
        self.assertIsNone(self.show('E2')['usage']['provider_reported_cost_usd'])
        self.prepare('E3','--repeat','--only','one')
        self.cli('run','E3','--max-cost-usd','0.6','--max-request-cost-usd','0.4',ok=False,
                 env={'FAKE_RUNNER_RESULT_OVERRIDE':json.dumps({'response_metadata':{'usage':{'cost':0.5}}})})
        self.cli('run','E3','--max-cost-usd','0.6','--max-request-cost-usd','0.4',ok=False)

    def test_missing_billing_keeps_reservation_without_stopping_provider_retry(self):
        spec=json.loads(self.spec.read_text())
        spec['runner'].update(provider='openrouter',concurrency=1)
        self.spec.write_text(json.dumps(spec))
        self.prepare()
        self.cli('run','E1','--max-cost-usd','1.2','--max-request-cost-usd','0.4',
                 env={'FAKE_RUNNER_FAILURES':json.dumps({'Tea':{'attempts':1,
                     'metadata':{'http_status':502}}})})
        self.assertEqual(len(self.calls()),3)
        self.assertEqual(self.show()['summary']['valid'],2)
        self.assertIsNone(self.show()['usage']['provider_reported_cost_usd'])
        self.cli('run','E1','--max-cost-usd','1.2','--max-request-cost-usd','0.4')
        self.assertEqual(len(self.calls()),3)

    def test_systemone_reuse_verifies_local_schema_without_wire_schema(self):
        self.prompt.write_text('{"state":"{POST}","questions":{"x":{"type":"noul","instructions":"Food?"}}}')
        self.write('cases.json', {'cases':[{'id':'one','inputs':{'POST':'Tea'}}]})
        spec = json.loads(self.spec.read_text())
        spec['runner'].update(provider='openrouter', model='typesafe/jev-1.13', reasoning_effort='provider-default',
                              output_schema={'type':'object','required':['x']})
        self.write('spec.json', spec)
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE':'{"x":{"type":"noul","noul":0.9}}',
            'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({'request': {
                'url':'http://127.0.0.1:18743/openrouter/api/v1/systemone',
                'body':{'model':'typesafe/jev-1.13', 'state':'Tea',
                        'questions':{'x':{'type':'noul','instructions':'Food?'}}}}})})
        before = len(self.calls())
        self.cli('prepare', 'E2', '--from', 'E1')
        self.cli('run', 'E2')
        self.assertEqual(len(self.calls()), before)
        self.assertEqual(self.show('E2')['summary']['reused'], 1)
        from sse_multivector import extraction_pipeline as engine
        history = engine.RequestHistory(self.root)
        manifest = json.loads((self.root/'E1/run/manifest.json').read_text())
        key = engine._prompt_request_key(manifest, manifest['prompts'][0]['text'])
        next(history.matches(key))
        saved = json.loads((self.root/'E1/runner-config.json').read_text())
        saved['output_schema'] = {'type':'object','required':['changed']}
        self.write('E1/runner-config.json', saved)
        with self.assertRaises(engine.RunnerError):
            next(history.matches(key))
        failed = self.cli('prepare', 'E3', '--from', 'E2', ok=False)
        self.assertIn('cannot verify request history source', failed.stderr)

    def test_systemone_wire_receipt_binds_exact_state_questions_and_local_schema(self):
        import copy
        from types import SimpleNamespace
        from sse_multivector import extraction_pipeline as engine
        state = {"state": "Coffee", "questions": {"x": {"type": "noul", "instructions": "Is this food?"}}}
        prompt = json.dumps(state)
        config = SimpleNamespace(provider="openrouter", model="typesafe/jev-1.13", reasoning_effort="provider-default")
        identity = {"runner_version": "oracle-model-runner/1", "runner_sha256": "e" * 64}
        output = {"x": {"type": "noul", "noul": 0.4}}
        schema = {"type": "object"}
        result = {**identity, "provider": config.provider, "model": config.model,
            "reasoning": config.reasoning_effort, "prompt_sha256": engine._sha256_bytes(prompt.encode()),
            "schema_sha256": engine._sha256_bytes(engine._ordered_json_bytes(schema)),
            "valid": True, "stop_reason": "stop", "http_attempts": 1, "error": None,
            "raw_text": json.dumps(output), "output": output,
            "request": {"url": "http://127.0.0.1:18743/openrouter/api/v1/systemone",
                "body": {"model": config.model, **state}}}
        engine._validate_model_result(config, config, prompt, schema, identity, result)
        for key, value in [("state", "Tea"), ("questions", {}), ("messages", [])]:
            changed = copy.deepcopy(result)
            changed["request"]["body"][key] = value
            with self.assertRaises(engine.RunnerError):
                engine._validate_model_result(config, config, prompt, schema, identity, changed)

    def test_saved_v32_titles_import_read_only_when_local_artifacts_exist(self):
        source = CLI.parent / "hierarchy-refresh-v1/source-packets.json"
        base = CLI.parent / "hdbv2-node-description-probe-v32/robustness-v1"
        if not (source.is_file() and (base / "config.json").is_file()):
            self.skipTest("local v32 experiment artifacts unavailable")
        config = json.loads((base / "config.json").read_text())
        plan = json.loads((base / "plan.json").read_text())
        spec = {
            "schema_version": 1,
            "prompt": {"id": "v32", "path": str(base.parent / "prompt.txt")},
            "dataset": {
                "adapter": "titles",
                "path": str(source),
                "select": plan["groups"],
            },
            "runner": {
                k: v
                for k, v in config.items()
                if k not in {"schema_version", "prompts", "run_directory"}
            },
        }
        self.spec.write_text(json.dumps(spec))
        before = (base / "run/results.jsonl").read_bytes()
        self.prepare("imported", "--import-config", base / "config.json")
        report = self.show("imported")
        self.assertEqual(report["summary"]["valid"], 20)
        self.assertEqual((base / "run/results.jsonl").read_bytes(), before)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
