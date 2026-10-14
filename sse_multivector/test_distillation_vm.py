"""Verification reuse must follow production input and evidence checks."""
import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_vm as vm


class VerificationFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / 'package'
        vm.prepare_package(Path(vm.__file__).resolve().parents[1], self.package)
        self.directory = self.root / 'vm'
        self.directory.mkdir()
        self.runtime = 'sha256:runtime'

    def stage(self, attempt, name, key):
        directory = attempt / 'results' / 'stages' / name
        directory.mkdir(parents=True)
        (directory / 'stage.log').write_text('passed\n')
        (directory / 'answer.json').write_text('{"answer": 1}\n')
        subprocess.run(['bash', '-se'], input=vm.receipt_script(directory, key, self.runtime),
                       text=True, check=True)
        return directory

    def cached(self):
        keys = vm.verification_keys(self.package)
        attempt = self.directory / 'attempt-1'
        for name, key in keys['stages'].items():
            self.stage(attempt, name, key)
        return attempt, keys

class VerificationCacheTests(VerificationFixture, unittest.TestCase):
    def test_clean_build_context_imports_without_a_sibling_runner_checkout(self):
        environment = {k: v for k, v in os.environ.items() if k != 'EXPERIMENT_RUNNER_ROOT'}
        script = "import sys; sys.path.insert(0, sys.argv[1]); " \
                 "from sse_multivector import distillation_run, distillation_deploy; " \
                 "assert distillation_run.parse_subjects('{\"subjects\":[]}') == []; " \
                 "assert 'experiment_runner/mask_positions.py' in distillation_deploy.code_hashes()"
        result = subprocess.run([sys.executable, '-I', '-c', script, str(self.package)],
            cwd=self.root, env=environment, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_parser_change_invalidates_every_runtime_stage(self):
        _, keys = self.cached()
        with (self.package / 'experiment_runner/mask_positions.py').open('a') as output:
            output.write('\n# changed shared parser\n')
        current = vm.verification_keys(self.package)
        self.assertTrue(all(current['stages'][key] != value for key, value in keys['stages'].items()))

    def test_unchanged_successful_stages_are_reused_automatically(self):
        attempt, keys = self.cached()
        plan = vm.verification_plan(self.directory, keys)
        self.assertEqual(plan, {name: attempt / 'results' / 'stages' / name for name in keys['stages']})

    def test_full_mode_ignores_successful_stage_evidence(self):
        _, keys = self.cached()
        self.assertEqual(vm.verification_plan(self.directory, keys, full=True), {})

    def test_controller_change_reruns_deployment_but_reuses_model_checks(self):
        attempt, _ = self.cached()
        with (self.package / 'vast/runner.py').open('a') as output:
            output.write('\n# changed controller\n')
        keys = vm.verification_keys(self.package)
        self.assertEqual(vm.verification_plan(self.directory, keys), {
            name: attempt / 'results' / 'stages' / name for name in ('candidates', 'workflow')})

    def test_missing_or_corrupt_evidence_is_not_reused(self):
        attempt, keys = self.cached()
        (attempt / 'results/stages/workflow/answer.json').write_text('corrupted')
        (attempt / 'results/stages/candidates/stage.log').unlink()
        self.assertEqual(set(vm.verification_plan(self.directory, keys)), {'deployment'})

    def test_runtime_dependency_or_unknown_file_change_invalidates_every_stage(self):
        _, keys = self.cached()
        for path in ('sse_multivector/distillation/requirements.lock', 'unclassified.py'):
            with self.subTest(path=path):
                target = self.package / path
                original = target.read_bytes() if target.exists() else None
                target.write_bytes(b'changed')
                changed = vm.verification_keys(self.package)
                self.assertTrue(all(changed['stages'][name] != key for name, key in keys['stages'].items()))
                if original is None:
                    target.unlink()
                else:
                    target.write_bytes(original)

    def test_model_and_test_changes_invalidate_all_dependent_stages(self):
        _, keys = self.cached()
        for name in vm.MODEL_FILES:
            with self.subTest(name=name):
                path = self.package / name
                original = path.read_bytes()
                path.write_bytes(original + b'\n# changed\n')
                self.assertEqual(vm.verification_plan(self.directory, vm.verification_keys(self.package)), {})
                path.write_bytes(original)

    def test_preflight_content_change_only_invalidates_deployment(self):
        preflight = self.root / 'preflight'
        preflight.mkdir()
        (preflight / 'input.json').write_text('first input')
        keys = vm.verification_keys(self.package, preflight)
        attempt = self.directory / 'attempt-1'
        for name, key in keys['stages'].items():
            self.stage(attempt, name, key)
        (preflight / 'input.json').write_text('changed input')
        changed = vm.verification_keys(self.package, preflight)
        self.assertNotEqual(changed['all'], keys['all'])
        self.assertEqual(set(vm.verification_plan(self.directory, changed)), {'candidates', 'workflow'})

    def test_actual_runtime_change_prevents_reuse(self):
        _, keys = self.cached()
        self.assertEqual(vm.verification_plan(self.directory, keys, runtime='different-runtime'), {})

    def test_unsealed_failed_stage_and_added_or_symlinked_files_are_rejected(self):
        attempt, keys = self.cached()
        root = attempt / 'results/stages'
        (root / 'candidates/passed.json').unlink()
        (root / 'workflow/unrecorded.txt').write_text('unrecorded')
        (root / 'deployment/link').symlink_to(root / 'deployment/answer.json')
        self.assertEqual(vm.verification_plan(self.directory, keys), {})

    def complete(self):
        attempt, keys = self.cached()
        results = attempt / 'results'
        for name in vm.ARTIFACTS:
            (results / name).write_text(name)
        artifacts = {name: vm.sha256(results / name) for name in vm.ARTIFACTS}
        vm.write_json(attempt / 'verification.json', {'keys': keys, 'runtime': self.runtime})
        vm.write_json(attempt / 'complete.json', {'status': 'passed', 'vm_stopped': True,
            'artifacts': artifacts, 'container_sha256': artifacts['container.tar.gz']})
        return attempt, keys

    def test_exact_completed_cache_hit_does_not_boot_or_require_vm_tools(self):
        attempt, _ = self.complete()
        with patch.object(vm.shutil, 'which', side_effect=AssertionError('VM tools checked')):
            self.assertEqual(vm.execute(self.directory, self.root / 'base-cache'), attempt)
        self.assertEqual(list(self.directory.glob('attempt-*')), [attempt])

    def test_full_mode_and_corrupt_archive_reject_completed_cache(self):
        attempt, keys = self.complete()
        self.assertIsNone(vm.complete_attempt(self.directory, keys, full=True))
        (attempt / 'results/container.tar.gz').write_text('corrupted archive')
        self.assertIsNone(vm.complete_attempt(self.directory, keys))
        self.assertEqual(set(vm.verification_plan(self.directory, keys)), set(vm.STAGES))

    def test_cli_full_option_reaches_production_runner(self):
        with patch.object(sys, 'argv', ['distillation_vm', '--directory', str(self.directory), '--full']), \
                patch.object(vm, 'execute') as execute, patch.object(vm.signal, 'signal'):
            vm.main()
        self.assertTrue(execute.call_args.kwargs['full'])


class StageExecutionTests(VerificationFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        docker = self.bin / 'docker'
        docker.write_text("#!/bin/sh\n[ -z \"$FAIL_EXPORT\" ] || exit 1\nprintf 'image archive'\n")
        docker.chmod(0o755)
        self.ssh = ['bash', '-c', 'eval "$1"', 'local-ssh']
        self.scp = [sys.executable, '-B', '-c',
                    'import shutil,sys; from pathlib import Path; '
                    'source=Path(sys.argv[-2]); target=Path(sys.argv[-1].split(":",1)[1])/source.name; '
                    'shutil.copytree(source,target)']
        self.image = {'RootFS': {'Layers': ['runtime-layer', 'source-1', 'source-2', 'source-3', 'source-4']},
                      'Architecture': 'amd64', 'Os': 'linux', 'Config': {}}
        self.build = 'mkdir -p "$result_dir"\ncat >"$result_dir/image.json" <<IMAGE\n' + json.dumps([self.image]) + '\nIMAGE\n'
        self.build += 'cat >"$result_dir/runtime.json" <<RUNTIME\n' + json.dumps([{'Id': self.runtime}]) + '\nRUNTIME\n'
        self.scripts = {
            'candidates': 'echo candidates passed\n',
            'workflow': 'mkdir -p "$result_dir/workflow"; echo fixture >"$result_dir/workflow/input"\n',
            'deployment': 'test "$(cat "$result_dir/workflow/input")" = fixture\necho deployment passed\n'}
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {'PATH': str(self.bin) + ':' + os.environ['PATH'], 'FAIL_EXPORT': ''}).start()
        patch.object(vm, 'BUILD_SCRIPT', self.build).start()
        patch.object(vm, 'STAGE_SCRIPTS', self.scripts).start()

    def run_checks(self, name, full=False):
        attempt = self.directory / name
        attempt.mkdir()
        remote = self.root / ('remote-' + name)
        try:
            return vm.run_checks(self.ssh, self.scp, attempt, str(remote),
                                 vm.verification_keys(self.package), full)
        finally:
            if remote.exists():
                shutil.copytree(remote, attempt / 'results')

    def test_failed_command_aborts_stage_and_never_seals_it(self):
        self.scripts['candidates'] = 'false\necho bad >"$result_dir/should-not-exist"\n'
        with self.assertRaisesRegex(RuntimeError, 'VM command failed'):
            self.run_checks('attempt-failed')
        result = self.directory / 'attempt-failed/results/stages/candidates'
        self.assertFalse((result / 'passed.json').exists())
        self.assertFalse((result / 'should-not-exist').exists())

    def test_export_failure_reuses_all_completed_tests_on_retry(self):
        os.environ['FAIL_EXPORT'] = '1'
        with self.assertRaisesRegex(RuntimeError, 'VM command failed'):
            self.run_checks('attempt-1')
        keys = vm.verification_keys(self.package)
        self.assertEqual(set(vm.verification_plan(self.directory, keys)), set(vm.STAGES))
        self.assertFalse((self.directory / 'attempt-1/results/container.tar.gz').exists())
        os.environ['FAIL_EXPORT'] = ''
        result = self.run_checks('attempt-2')
        self.assertTrue(all(stage['reused_from'] for stage in result['stages'].values()))
        self.assertTrue((self.directory / 'attempt-2/results/container.tar.gz').is_file())

    def test_full_mode_runs_all_stages_after_success(self):
        self.run_checks('attempt-1')
        result = self.run_checks('attempt-2', full=True)
        self.assertTrue(all(stage['reused_from'] is None for stage in result['stages'].values()))

    def test_cleanup_finishes_before_success_receipt_is_written(self):
        self.scripts['candidates'] = 'trap \'echo cleanup >"$result_dir/cleanup.txt"\' EXIT\necho passed\n'
        self.run_checks('attempt-1')
        directory = self.directory / 'attempt-1/results/stages/candidates'
        self.assertTrue(vm.valid_stage(directory, vm.verification_keys(self.package)['stages']['candidates']))
        self.assertIn('cleanup.txt', json.loads((directory / 'passed.json').read_text())['files'])

    def test_changed_runtime_reruns_stages_with_unchanged_code(self):
        self.run_checks('attempt-1')
        with patch.object(vm, 'BUILD_SCRIPT', self.build.replace(self.runtime, 'different-runtime')):
            result = self.run_checks('attempt-2')
        self.assertTrue(all(stage['reused_from'] is None for stage in result['stages'].values()))


if __name__ == '__main__':
    unittest.main()
