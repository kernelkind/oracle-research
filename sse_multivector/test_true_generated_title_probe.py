"""TRUE03 production-path tests; no model loading or inference."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import true_category_probe
import true_generated_title_probe as probe
import true_holdout_probe


def titles():
    return {'groups': [{'group': 'A', 'title': '  Exact | title\ntext  '},
                       {'group': 'B', 'title': 'Second title'},
                       {'group': 'C', 'title': 'Third title'}]}


def fixture():
    return dict(experiment='TRUE03', threshold=0.142, source_titles_sha256='a' * 64,
        pairs=[dict(id='P01', a_id='A', b_id='B', a_contains_b=True,
                    b_contains_a=False, rationale='A contains B, not the reverse.')])


class TRUEGeneratedTitleProbeTests(unittest.TestCase):
    def test_both_directions_use_exact_generated_titles(self):
        data, source = fixture(), titles()
        before = copy.deepcopy((data, source))
        rows = probe.prepare_inputs(data, source)
        self.assertEqual((data, source), before)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['a'], '  Exact | title\ntext  ')
        self.assertEqual(rows[0]['b'], 'Second title')
        self.assertEqual(rows[1]['a'], rows[0]['b'])
        self.assertEqual(rows[1]['b'], rows[0]['a'])
        self.assertIs(rows[0]['expected'], True)
        self.assertIs(rows[1]['expected'], False)
        self.assertEqual(rows[0]['a_id'], 'A')
        self.assertEqual(rows[0]['b_id'], 'B')
        self.assertEqual(rows[1]['a_id'], 'B')
        self.assertEqual(rows[1]['b_id'], 'A')
        self.assertEqual(len({row['id'] for row in rows}), 2)
        for row in rows:
            self.assertEqual(row['domain'], 'generated-titles')
            self.assertEqual(row['format'], 'topic')
            self.assertEqual(row['model_input'], true_category_probe.model_input(row, 'topic'))
            self.assertNotIn(data['pairs'][0]['rationale'], row['model_input'])
            self.assertNotIn('expected', row['model_input'])

    def test_relation_kinds_require_both_explicit_boolean_judgments(self):
        for forward, reverse, kinds in (
                (True, False, ('strict-containment', 'reversed-containment')),
                (False, True, ('reversed-containment', 'strict-containment')),
                (True, True, ('equivalent', 'equivalent')),
                (False, False, ('noncontaining', 'noncontaining'))):
            data = fixture()
            data['pairs'][0].update(a_contains_b=forward, b_contains_a=reverse)
            rows = probe.prepare_inputs(data, titles())
            self.assertEqual(tuple(row['kind'] for row in rows), kinds)
            self.assertEqual(tuple(row['expected'] for row in rows), (forward, reverse))
        for key in ('a_contains_b', 'b_contains_a'):
            for value in (None, 0, 1, 'true', [], {}):
                data = fixture()
                data['pairs'][0][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    probe.prepare_inputs(data, titles())
            data = fixture()
            del data['pairs'][0][key]
            with self.assertRaises(ValueError):
                probe.prepare_inputs(data, titles())

    def test_invalid_fixture_pairs_and_title_groups_are_rejected(self):
        fixture_mutations = [
            lambda d: d.update(experiment='TRUE02'),
            lambda d: d.update(threshold=0.14),
            lambda d: d.update(source_titles_sha256='not-a-hash'),
            lambda d: d.pop('source_titles_sha256'),
            lambda d: d.update(pairs=[]),
            lambda d: d.update(pairs={}),
            lambda d: d['pairs'].append(None),
            lambda d: d['pairs'][0].update(id=''),
            lambda d: d['pairs'][0].update(id=[]),
            lambda d: d['pairs'][0].update(a_id='unknown'),
            lambda d: d['pairs'][0].update(a_id=[]),
            lambda d: d['pairs'][0].update(a_id='B'),
            lambda d: d['pairs'][0].update(rationale=' \n '),
            lambda d: d['pairs'][0].pop('rationale'),
            lambda d: d['pairs'].append(dict(d['pairs'][0], b_id='C')),
            lambda d: d['pairs'].append(dict(d['pairs'][0], id='P02')),
            lambda d: d['pairs'].append(dict(d['pairs'][0], id='P02', a_id='B', b_id='A')),
        ]
        for index, mutate in enumerate(fixture_mutations):
            data = fixture()
            mutate(data)
            with self.subTest(fixture_mutation=index), self.assertRaises(ValueError):
                probe.prepare_inputs(data, titles())
        title_mutations = [
            lambda d: d.update(groups=[]),
            lambda d: d.update(groups={}),
            lambda d: d['groups'].append(None),
            lambda d: d['groups'].append(dict(d['groups'][0])),
            lambda d: d['groups'][0].update(group=[]),
            lambda d: d['groups'][0].update(group=''),
            lambda d: d['groups'][0].update(title=' \n '),
            lambda d: d['groups'][0].update(title=None),
        ]
        for index, mutate in enumerate(title_mutations):
            source = titles()
            mutate(source)
            with self.subTest(title_mutation=index), self.assertRaises(ValueError):
                probe.prepare_inputs(fixture(), source)

    def test_freeze_saves_exact_fixture_titles_inputs_and_all_runner_sources(self):
        title_bytes = ('  ' + json.dumps(titles()) + '\n').encode()
        data = fixture()
        data['source_titles_sha256'] = hashlib.sha256(title_bytes).hexdigest()
        fixture_bytes = ('  ' + json.dumps(data) + '\n').encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, title_source, output = root / 'fixture.json', root / 'titles.json', root / 'run'
            source.write_bytes(fixture_bytes)
            title_source.write_bytes(title_bytes)
            rows = probe.freeze_inputs(source, probe.sha256(source), title_source, output)
            self.assertEqual((output / 'fixture.json').read_bytes(), fixture_bytes)
            self.assertEqual((output / 'titles.json').read_bytes(), title_bytes)
            self.assertEqual(json.loads((output / 'inputs.json').read_text()), rows)
            started = json.loads((output / 'started.json').read_text())
            self.assertEqual(started['experiment'], 'TRUE03')
            self.assertEqual(started['python_version'], sys.version)
            self.assertEqual(started['python_executable'], sys.executable)
            self.assertEqual(started['threshold'], 0.142)
            self.assertEqual(started['pairs'], 2)
            self.assertEqual(started['fixture_sha256'], probe.sha256(source))
            self.assertEqual(started['source_titles_sha256'], probe.sha256(title_source))
            self.assertEqual(started['inputs_sha256'], probe.sha256(output / 'inputs.json'))
            for module in (probe, true_holdout_probe, true_category_probe,
                           true_holdout_probe.hierarcaps_mask_probe):
                path = Path(module.__file__)
                self.assertEqual((output / path.name).read_bytes(), path.read_bytes())
                self.assertEqual(started['source_sha256'][path.name], probe.sha256(path))
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            with self.assertRaises(FileExistsError):
                probe.freeze_inputs(source, probe.sha256(source), title_source, output)
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, before)

    def test_bad_hash_or_duplicate_json_keys_never_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, title_source, output = root / 'fixture.json', root / 'titles.json', root / 'run'
            title_source.write_text(json.dumps(titles()))
            data = fixture()
            data['source_titles_sha256'] = probe.sha256(title_source)
            source.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'fixture'):
                probe.freeze_inputs(source, '0' * 64, title_source, output)
            self.assertFalse(output.exists())
            title_source.write_text(json.dumps(titles()) + '\n')
            with self.assertRaisesRegex(ValueError, 'title'):
                probe.freeze_inputs(source, probe.sha256(source), title_source, output)
            self.assertFalse(output.exists())
            title_source.write_text('{"groups":[],"groups":[]}')
            data['source_titles_sha256'] = probe.sha256(title_source)
            source.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                probe.freeze_inputs(source, probe.sha256(source), title_source, output)
            self.assertFalse(output.exists())
            source.write_text('{"experiment":"TRUE03","experiment":"TRUE03"}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                probe.freeze_inputs(source, probe.sha256(source), title_source, output)
            self.assertFalse(output.exists())

    def test_true02_summary_and_report_work_for_generated_title_rows(self):
        rows = probe.prepare_inputs(fixture(), titles())
        for row, score in zip(rows, (0.9, 0.142)):
            row.update(predicted=row['expected'], entailment_score=score,
                       threshold_predicted=true_holdout_probe.threshold_decision(score))
        summary = true_holdout_probe.summarize(rows)
        self.assertEqual(summary['overall']['native']['correct'], 2)
        self.assertEqual(summary['overall']['cutoff']['correct'], 2)
        self.assertEqual(summary['unordered_pairs']['overall']['total'], 1)
        report = true_holdout_probe.render_decisions(rows, experiment='TRUE03')
        self.assertTrue(report.startswith('# TRUE03'))
        self.assertNotIn('TRUE02', report)
        self.assertTrue(true_holdout_probe.render_decisions(rows).startswith('# TRUE02'))
        self.assertIs(probe.run_inference, true_holdout_probe.run_inference)

    def test_cli_help_and_invalid_snapshot_do_not_load_model(self):
        command = [sys.executable, probe.__file__]
        help_result = subprocess.run(command + ['--help'], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for option in ('--fixture', '--fixture-sha256', '--titles', '--output', '--snapshot', '--batch-size'):
            self.assertIn(option, help_result.stdout)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'run'
            result = subprocess.run(command + ['--fixture', str(root / 'missing-fixture'),
                '--fixture-sha256', 'a' * 64, '--titles', str(root / 'missing-titles'),
                '--output', str(output), '--snapshot', str(root)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('exact pinned model snapshot required', result.stderr)
            self.assertFalse(output.exists())

    def test_cli_freezes_before_rejecting_missing_checkpoint_and_preserves_interrupted_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, title_source, output = root / 'fixture.json', root / 'titles.json', root / 'run'
            title_source.write_text(json.dumps(titles()))
            data = fixture()
            data['source_titles_sha256'] = probe.sha256(title_source)
            source.write_text(json.dumps(data))
            snapshot = root / ('models--' + probe.MODEL_ID.replace('/', '--')) / 'snapshots' / probe.REVISION
            snapshot.mkdir(parents=True)
            command = [sys.executable, probe.__file__, '--fixture', str(source),
                '--fixture-sha256', probe.sha256(source), '--titles', str(title_source),
                '--output', str(output), '--snapshot', str(snapshot)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('weight shard differs from the release manifest', result.stderr)
            self.assertIn('Frozen 2 inputs before inference', result.stdout)
            self.assertTrue((output / 'started.json').exists())
            self.assertEqual((output / 'fixture.json').read_bytes(), source.read_bytes())
            self.assertEqual((output / 'titles.json').read_bytes(), title_source.read_bytes())
            self.assertFalse((output / 'model-files.json').exists())
            self.assertFalse((output / 'config.json').exists())
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            retry = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertIn('output exists', retry.stderr)
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, before)


class TRUE02InferenceExtractionTests(unittest.TestCase):
    def test_shared_inference_is_exact_frozen_true02_block_except_parameters(self):
        """Guard the real inference code without loading or replacing the model."""
        frozen = Path(true_holdout_probe.__file__).parent / 'navigation-research-v1/TRUE02/true_holdout_probe.py'
        old_module = ast.parse(frozen.read_text())
        old_main = next(node for node in old_module.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'main')
        start = next(index for index, node in enumerate(old_main.body)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                     and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print')

        class Parameters(ast.NodeTransformer):
            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name) and node.value.id == 'args':
                    if node.attr in ('output', 'batch_size'):
                        return ast.Name(id=node.attr, ctx=node.ctx)
                return self.generic_visit(node)

            def visit_Constant(self, node):
                return ast.Name(id='experiment', ctx=ast.Load()) if node.value == 'TRUE02' else node

            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == 'render_decisions':
                    node.keywords.append(ast.keyword(arg='experiment', value=ast.Name(
                        id='experiment', ctx=ast.Load())))
                return node

        expected = Parameters().visit(ast.Module(body=old_main.body[start:], type_ignores=[]))
        new_module = ast.parse(Path(true_holdout_probe.__file__).read_text())
        shared = next(node for node in new_module.body
                      if isinstance(node, ast.FunctionDef) and node.name == 'run_inference')
        actual = ast.Module(body=shared.body, type_ignores=[])
        self.assertEqual(ast.dump(actual), ast.dump(expected))
        old_entrypoint = next(node for node in new_module.body
                              if isinstance(node, ast.FunctionDef) and node.name == 'main')
        self.assertTrue(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                            and node.func.id == 'run_inference' for node in ast.walk(old_entrypoint)))


if __name__ == '__main__':
    unittest.main()
