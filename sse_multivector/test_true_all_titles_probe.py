"""TRUE04 production-path tests; no checkpoint loading or model replacement."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import true_category_probe
import true_holdout_probe


def titles():
    groups = [dict(group=f'S{index:010x}', title=f'Generated title {index}')
              for index in range(61)]
    groups[0]['title'] = '  Exact | title\ntext  '
    groups[1]['title'] = groups[2]['title']
    return dict(groups=groups)


class TRUEAllTitlesProbeTests(unittest.TestCase):
    def setUp(self):
        self.probe = importlib.import_module('true_all_titles_probe')

    def test_all_3660_distinct_group_directions_preserve_source_order_and_exact_titles(self):
        source = titles()
        before = copy.deepcopy(source)
        rows = self.probe.prepare_inputs(source)
        self.assertEqual(source, before)
        self.assertEqual(len(rows), 3660)
        self.assertEqual(len({row['id'] for row in rows}), 3660)
        self.assertEqual([(row['a_id'], row['b_id']) for row in rows],
                         [(a['group'], b['group']) for a in source['groups']
                          for b in source['groups'] if a['group'] != b['group']])
        by_id = {group['group']: group['title'] for group in source['groups']}
        for row in rows:
            self.assertEqual(row['a'], by_id[row['a_id']])
            self.assertEqual(row['b'], by_id[row['b_id']])
            self.assertEqual(row['model_input'], true_category_probe.model_input(row, 'topic'))
            self.assertEqual(row['format'], 'topic')
            self.assertEqual(row['domain'], 'generated-titles')
            self.assertNotIn('expected', row)
            self.assertNotIn('kind', row)
        self.assertTrue(any(row['a'] == row['b'] for row in rows))
        self.assertIs(self.probe.run_inference, true_holdout_probe.run_inference)

    def test_invalid_titles_are_rejected_without_filtering_or_repair(self):
        mutations = [lambda d: d.update(groups=[]),
                     lambda d: d['groups'].pop(),
                     lambda d: d['groups'].append(dict(group='extra', title='Extra')),
                     lambda d: d['groups'].__setitem__(0, None),
                     lambda d: d['groups'][0].update(group=[]),
                     lambda d: d['groups'][0].update(group='  '),
                     lambda d: d['groups'][0].update(group=d['groups'][1]['group']),
                     lambda d: d['groups'][0].update(title=None),
                     lambda d: d['groups'][0].update(title=' \n ')]
        for index, mutate in enumerate(mutations):
            source = titles()
            mutate(source)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                self.probe.prepare_inputs(source)
        for source in (None, [], {}, {'groups': {}}):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.probe.prepare_inputs(source)

    def test_freeze_persists_exact_bytes_inputs_settings_and_source_hashes(self):
        raw = ('  ' + json.dumps(titles(), ensure_ascii=False) + '\n').encode()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'titles.json', root / 'run'
            source.write_bytes(raw)
            rows = self.probe.freeze_inputs(source, digest, output)
            self.assertEqual((output / 'titles.json').read_bytes(), raw)
            self.assertEqual(json.loads((output / 'inputs.json').read_text()), rows)
            started = json.loads((output / 'started.json').read_text())
            self.assertEqual(started['experiment'], 'TRUE04')
            self.assertEqual(started['source_titles_sha256'], digest)
            self.assertEqual(started['pairs'], 3660)
            self.assertEqual(started['unordered_pairs'], 1830)
            self.assertEqual(started['groups'], 61)
            self.assertEqual(started['batch_size'], 4)
            self.assertEqual(started['dtype'], 'float32')
            self.assertEqual(started['device'], 'cpu')
            self.assertEqual(started['threads'], 4)
            self.assertEqual(started['threshold'], 0.142)
            self.assertEqual(started['python_version'], sys.version)
            self.assertEqual(started['python_executable'], sys.executable)
            self.assertEqual(started['inputs_sha256'], self.probe.sha256(output / 'inputs.json'))
            for module in (self.probe, true_holdout_probe, true_category_probe,
                           true_holdout_probe.hierarcaps_mask_probe):
                path = Path(module.__file__)
                self.assertEqual((output / path.name).read_bytes(), path.read_bytes())
                self.assertEqual(started['source_sha256'][path.name], self.probe.sha256(path))
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            with self.assertRaises(FileExistsError):
                self.probe.freeze_inputs(source, digest, output)
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, before)

    def test_bad_hash_or_duplicate_json_keys_never_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'titles.json', root / 'run'
            source.write_text(json.dumps(titles()))
            with self.assertRaisesRegex(ValueError, 'title'):
                self.probe.freeze_inputs(source, '0' * 64, output)
            self.assertFalse(output.exists())
            source.write_text('{"groups": [], "groups": []}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                self.probe.freeze_inputs(source, self.probe.sha256(source), output)
            self.assertFalse(output.exists())

    def test_cli_prepare_only_freezes_without_a_model_and_refuses_overwrite(self):
        command = [sys.executable, self.probe.__file__]
        help_result = subprocess.run(command + ['--help'], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for option in ('--titles', '--titles-sha256', '--output', '--snapshot', '--prepare-only'):
            self.assertIn(option, help_result.stdout)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'titles.json', root / 'run'
            source.write_text(json.dumps(titles()))
            command += ['--titles', str(source), '--titles-sha256', self.probe.sha256(source),
                        '--output', str(output), '--prepare-only']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / 'started.json').exists())
            self.assertFalse((output / 'model-files.json').exists())
            self.assertFalse((output / 'config.json').exists())
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            retry = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertIn('output exists', retry.stderr)
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, before)

    def test_cli_snapshot_validation_and_checkpoint_failure_preserve_frozen_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'titles.json', root / 'run'
            source.write_text(json.dumps(titles()))
            command = [sys.executable, self.probe.__file__, '--titles', str(source),
                       '--titles-sha256', self.probe.sha256(source), '--output', str(output)]
            missing = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn('--snapshot', missing.stderr)
            self.assertFalse(output.exists())
            invalid = subprocess.run(command + ['--snapshot', str(root)],
                                     capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn('exact pinned model snapshot required', invalid.stderr)
            self.assertFalse(output.exists())
            snapshot = root / ('models--' + self.probe.MODEL_ID.replace('/', '--')) / 'snapshots' / self.probe.REVISION
            snapshot.mkdir(parents=True)
            result = subprocess.run(command + ['--snapshot', str(snapshot)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('weight shard differs from the release manifest', result.stderr)
            self.assertIn('Frozen 3660 inputs before inference', result.stdout)
            self.assertEqual((output / 'titles.json').read_bytes(), source.read_bytes())
            self.assertTrue((output / 'started.json').exists())
            self.assertFalse((output / 'model-files.json').exists())
            self.assertFalse((output / 'config.json').exists())


class TRUEUnlabeledResultsTests(unittest.TestCase):
    def test_shared_summary_and_report_accept_rows_without_an_answer_key(self):
        rows = [dict(id='A-contains-B', domain='generated-titles', a_id='A', b_id='B',
                     a='A', b='B', format='topic', predicted=True, entailment_score=0.9,
                     threshold_predicted=True),
                dict(id='B-contains-A', domain='generated-titles', a_id='B', b_id='A',
                     a='B', b='A', format='topic', predicted=False, entailment_score=0.142,
                     threshold_predicted=False)]
        summary = true_holdout_probe.summarize(rows)
        self.assertFalse(summary['labeled'])
        self.assertEqual(summary['overall']['native'],
                         dict(total=2, yes=1, no=1, unresolved=0))
        self.assertEqual(summary['overall']['cutoff'], summary['overall']['native'])
        self.assertNotIn('accuracy', str(summary))
        report = true_holdout_probe.render_decisions(rows, experiment='TRUE04')
        self.assertTrue(report.startswith('# TRUE04'))
        self.assertNotIn('| Expected |', report)
        self.assertNotIn('errors', report)
        self.assertIn('No answer key', report)
        self.assertIn('A-contains-B', report)
        self.assertIn('B-contains-A', report)

    def test_partial_or_nonboolean_answer_keys_never_produce_reports(self):
        for rows in ([dict(expected=True), {}], [dict(expected=None)], [dict(expected=0)]):
            for function in (true_holdout_probe.summarize, true_holdout_probe.render_decisions):
                with self.subTest(rows=rows, function=function.__name__), self.assertRaisesRegex(
                        ValueError, 'answer key'):
                    function(rows)

    def test_unlabeled_summary_still_checks_frozen_cutoff_and_native_verdicts(self):
        row = dict(id='A-contains-B', a_id='A', b_id='B', domain='generated-titles',
                   a='A | title\ntext', b='B', predicted=None, entailment_score=0.142,
                   threshold_predicted=False)
        summary = true_holdout_probe.summarize([row])
        self.assertEqual(summary['overall']['native']['unresolved'], 1)
        report = true_holdout_probe.render_decisions([row], experiment='TRUE04')
        self.assertIn('A \\| title text', report)
        self.assertIn('Unresolved', report)
        self.assertIn('0.142000', report)
        with self.assertRaisesRegex(ValueError, 'cutoff'):
            true_holdout_probe.summarize([dict(row, threshold_predicted=True)])
        with self.assertRaisesRegex(ValueError, 'native'):
            true_holdout_probe.summarize([dict(row, predicted=0)])


if __name__ == '__main__':
    unittest.main()
