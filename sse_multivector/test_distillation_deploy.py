"""Exercise the production deployment package and SSH operator."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_deploy as deploy
from sse_multivector.distillation_run import read_json, write_json, sha256
from sse_multivector.test_distillation_data import DistillationDataTests


class PackageTests(unittest.TestCase):
    def test_unbounded_child_finishes_after_operator_interrupt(self):
        import signal
        import time
        with tempfile.TemporaryDirectory() as temporary:
            ready, done = Path(temporary) / 'ready', Path(temporary) / 'done'
            child = (f'from pathlib import Path; import time; Path({str(ready)!r}).touch(); '
                     f'time.sleep(.5); Path({str(done)!r}).touch()')
            parent = ('import sys; from sse_multivector.distillation_deploy import run_process; '
                      f'run_process([sys.executable, "-c", {child!r}], None)')
            process = subprocess.Popen([sys.executable, '-B', '-c', parent],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            try:
                deadline = time.monotonic() + 10
                while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(ready.exists())
                process.send_signal(signal.SIGINT)
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, stderr.decode())
                self.assertTrue(done.exists())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    def test_subjects_only_package_has_no_mask_prompt_dependency(self):
        from sse_multivector import distillation_data
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            distillation_data.prepare(root / 'source.json', root / 'annotations.json', root / 'subjects.txt',
                None, 'AS-test', None, 2, 'pilot', root / 'subject-data', tasks=('subjects',))
            model = root / 'model'
            model.mkdir()
            (model / 'weights').write_bytes(b'model payload')
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'subject-data'), 'model': str(model), 'revision': None,
                                'training_milestones': [1, 2, 4]})
            package = root / 'package'
            deploy.prepare([config], package, 600, through='preflight')
            job = deploy.verify_package(package)
            copied = read_json(package / job['runs'][0])
            self.assertNotIn('mask_prompt', copied)
            self.assertFalse((package / 'prompts').exists())

    def test_offer_checks_returned_storage_inclusive_price_and_total_budget(self):
        settings = read_json(Path(__file__).parent / "distillation/vast-launch.json")
        offer = {**settings["offer_equals"], **settings["offer_minimums"],
                 **settings["offer_maximums"], "id": 123, "driver_version": "595.58.03",
                 "dph_base": 1.5, "storage_cost": .24, "storage_total_cost": .1}
        self.assertEqual(deploy.check_offer(settings, offer)["maximum_charge_usd"], "24.60")
        for key, value in (("dph_total", 1.61), ("gpu_ram", 48000), ("inet_up_cost", float("nan")),
                           ("storage_total_cost", 0), ("driver_version", "570.00.00")):
            with self.subTest(field=key), self.assertRaises(ValueError):
                deploy.check_offer(settings, {**offer, key: value})

    def test_frozen_package_is_portable_and_rejects_changed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            model = root / "model"
            model.mkdir()
            (model / "weights").write_bytes(b"model payload")
            config = root / "candidate.json"
            write_json(config, {"data": str(root / "prepared"), "mask_prompt": str(root / "masks.txt"),
                                "model": str(model), "revision": None})
            package = root / "package"
            deploy.prepare([config], package, 600, through="preflight")
            job = deploy.verify_package(package)
            copied = read_json(package / job["runs"][0])
            for key in ("data", "mask_prompt", "model"):
                self.assertTrue(not Path(copied[key]).is_absolute())
                self.assertNotIn(str(root), copied[key])
            self.assertEqual(job["timeout_seconds"], 600)
            self.assertEqual(job["through"], "preflight")
            self.assertFalse(any(p.suffix == ".py" for p in package.rglob("*")))
            mask = package / copied["mask_prompt"]
            mask.write_text("changed")
            with self.assertRaisesRegex(ValueError, "manifest"):
                deploy.verify_package(package)



@unittest.skipUnless(os.environ.get('DISTILLATION_SSH_TARGET'), 'requires the local deployment VM')
class SharedSSHTests(unittest.TestCase):
    def test_chunked_copy_prioritizes_new_responses_over_real_ssh(self):
        import argparse
        import importlib.util
        sys.path.insert(0, str(deploy.CODE_ROOT / 'vast'))
        import package as packager
        from sse_multivector.distillation_vast import make_spec
        from sse_multivector.test_distillation_vast import quote
        root = self.fixture_package('chunked-copy')
        settings, offer = quote()
        spec = make_spec(settings, offer, root / 'inputs', settings['image_repository'] + '@sha256:' + '4' * 64)
        spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 8 * 1024 * 1024,
                                    'timeout_seconds': 120}
        ledger = root / 'ledger.json'
        write_json(ledger, {'lifetime_cap_cents': 100000, 'actual_spend_cents': 0,
                           'outstanding_commitments_cents': 0, 'reserved_remaining_work_cents': 0, 'entries': []})
        operation = root / 'operation'
        config = packager.freeze(spec, operation, ledger)
        definition = importlib.util.spec_from_file_location('chunked_ssh_runner', operation / 'transport/control/vast_full_build.py')
        module = importlib.util.module_from_spec(definition)
        sys.modules[definition.name] = module
        definition.loader.exec_module(module)
        context = module.Context.load(argparse.Namespace(root=operation, config=config, operation='copy'))
        self.assertIs(context.config['ssh_direct'], False)
        (operation / 'launch').mkdir()
        (operation / 'launch/operation-contract.json').write_bytes(config.read_bytes())
        target = read_json(os.environ['DISTILLATION_SSH_TARGET'])
        key, endpoint = Path(target['identity']), ['-p', str(target['port']), target['host']]
        module.tar_upload_directory(context, key, endpoint, operation / 'transport', '/workspace/oracle-full-build/transport')
        module.tar_upload_directory(context, key, endpoint, operation / 'launch', '/workspace/oracle-full-build/launch')
        module.completed_process([*module.ssh_arguments(context, key, endpoint), 'rm -rf /workspace/oracle-full-build/work'])
        checkpoint = root / 'checkpoint'
        checkpoint.mkdir()
        (checkpoint / 'weights.bin').write_bytes(b'c' * (128 * 1024 * 1024 + 1024))
        write_json(checkpoint / 'complete.json', {'weights.bin': sha256(checkpoint / 'weights.bin')})
        module.tar_upload_directory(context, key, endpoint, checkpoint, '/workspace/oracle-full-build/work/results/checkpoints/adapter')
        note = root / 'note'
        note.mkdir()
        (note / 'subjects.json').write_text('response published during checkpoint transfer')
        write_json(note / 'complete.json', {'subjects.json': sha256(note / 'subjects.json')})
        write_json(operation / 'progressive/endpoint.json', {'identity': str(key), 'target': endpoint})
        weights = operation / 'result.next/work/results/checkpoints/adapter/weights.bin'
        subject = operation / 'result.next/work/results/responses/note/subjects.json'
        stream, groups = module.stream_processes, []
        def copy(*args):
            stream(*args)
            if args[2] != 'progressive copy':
                return
            groups.append(read_json(operation / 'progressive/request.json'))
            self.assertLessEqual(sum(record['length'] for record in groups[-1]), 64 * 1024 * 1024)
            if len(groups) == 1:
                self.assertFalse(weights.exists())
                module.tar_upload_directory(context, key, endpoint, note, '/workspace/oracle-full-build/work/results/responses/note')
            elif len(groups) == 2:
                self.assertTrue(subject.is_file())
                self.assertFalse(weights.exists())
            if weights.exists():
                write_json(operation / 'progressive/terminal.json', {'attempt_id': '001'})
        with patch.object(module, 'stream_processes', side_effect=copy):
            self.assertEqual(module.progressive_copy(context, watch=True)['state'], 'stopped')
        self.assertEqual(len(groups), 3)
        self.assertEqual(sha256(weights), sha256(checkpoint / 'weights.bin'))
        self.assertEqual(sha256(subject), sha256(note / 'subjects.json'))
        write_json(root / 'transfer-checks.json', {'groups': groups, 'response_before_checkpoint': True,
                                                'checkpoint_sha256': sha256(weights), 'subject_sha256': sha256(subject)})

    def run_package(self, inputs, root, expected=0, stop=False, copy_while_running=False):
        import argparse
        import importlib.util
        import shutil
        import time
        sys.path.insert(0, str(deploy.CODE_ROOT / 'vast'))
        import package as packager
        import runner
        from sse_multivector.test_distillation_vast import quote
        from sse_multivector.distillation_vast import make_spec
        ledger = root.parent / (root.name + '-ledger.json')
        write_json(ledger, {'lifetime_cap_cents': 100000, 'actual_spend_cents': 0,
            'outstanding_commitments_cents': 0, 'reserved_remaining_work_cents': 0, 'entries': []})
        settings, offer = quote()
        if deploy.verify_package(inputs)['timeout_seconds'] is None:
            settings['worker_timeout_seconds'] = None
        spec = make_spec(settings, offer, inputs, settings['image_repository'] + '@sha256:' + '4' * 64)
        if copy_while_running:
            spec['progressive_copy'] = {'poll_seconds': 1, 'bytes_per_second': 1024 * 1024, 'timeout_seconds': 120}
        config = packager.freeze(spec, root, ledger)
        definition = importlib.util.spec_from_file_location('frozen_ssh_runner', root / 'transport/control/vast_full_build.py')
        module = importlib.util.module_from_spec(definition)
        sys.modules[definition.name] = module
        definition.loader.exec_module(module)
        context = module.Context.load(argparse.Namespace(root=root, config=config, operation='run'))
        target = read_json(os.environ['DISTILLATION_SSH_TARGET'])
        key = Path(target['identity'])
        endpoint = ['-p', str(target['port']), target['host']]
        # Provider receipts are fixture data; transport, worker, training and
        # retrieval below are the real frozen shared runner over real SSH.
        for name in ('approval-plan', 'approval', 'offer', 'create-result', 'instance', 'pre-transfer-instance-validation'):
            write_json(root / f'launch/{name}.json', {})
        shutil.copyfile(ledger, root / 'launch/reserved-budget-ledger.json')
        write_json(root / 'launch/full-build-reservation.json', {'ledger_sha256': sha256(ledger)})
        shutil.copyfile(config, root / 'launch/operation-contract.json')
        remote = '/workspace/oracle-full-build'
        module.verify_local_ssh(context)
        module.tar_upload_directory(context, key, endpoint, root / 'transport', remote + '/transport')
        module.tar_upload_directory(context, key, endpoint, root / 'launch', remote + '/launch')
        # Each independent test uses a fresh operation on the same SSH target.
        module.completed_process([*module.ssh_arguments(context, key, endpoint),
            'rm -rf /workspace/oracle-full-build/work /workspace/oracle-full-build/package /workspace/oracle-full-build/preparation-attempts'])
        def call(operation, *args):
            return module.remote_json(context, key, endpoint, operation, *args)
        self.assertTrue(call('_remote-verify-transfer')['verified'])
        deadline = time.monotonic() + 240
        while not call('_remote-prepare').get('prepared'):
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.2)
        call('_remote-worker', '--attempt', '001')
        copier = module.start_progressive_copy(context, key, endpoint) if copy_while_running else None
        if copier is not None:
            self.addCleanup(lambda: copier.terminate() if copier.poll() is None else None)
        copied_before_terminal = None
        if stop:
            time.sleep(2)
            call('_remote-stop', '--attempt', '001')
        while True:
            state = call('_remote-status', '--attempt', '001')
            if copier is not None and state['state'] == 'running':
                local = root / 'result.next/work/results/first'
                notes = list(local.glob('baseline/note-*/complete.json'))
                checkpoints = list(local.glob('checkpoints/checkpoint-*/complete.json'))
                if notes and checkpoints and copied_before_terminal is None:
                    from sse_multivector.distillation_run import verify_saved
                    self.assertTrue(all(verify_saved(p.parent) for p in notes + checkpoints))
                    copied_before_terminal = {str(p.relative_to(root / 'result.next')): p.stat().st_mtime_ns for p in notes + checkpoints}
                    write_json(root / 'copied-while-running.json', {'remote_state': state, 'files': copied_before_terminal})
            if state['state'] == 'terminal':
                break
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.5)
        (root / 'result.next').mkdir(exist_ok=True)
        module.ensure_retrieved(context, 'offline-fixture', key, endpoint, '001')
        if copier is not None:
            self.assertIsNotNone(copied_before_terminal, (root / 'progressive/copier.log').read_text())
            self.assertEqual(copier.wait(timeout=20), 0, (root / 'progressive/copier.log').read_text())
            receipt = read_json(root / 'launch/retrieval-verification.json')['progressive_copy']
            self.assertGreater(receipt['reused_files'], 0)
            self.assertGreater(receipt['reused_bytes'], 0)
            self.assertTrue(all((root / 'result.next' / p).stat().st_mtime_ns == stamp
                                for p, stamp in copied_before_terminal.items()))
            module.completed_process([*module.ssh_arguments(context, key, endpoint),
                'test -f /workspace/oracle-full-build/work/results/first/baseline/note-0000/subjects.json'])
        if expected == 0:
            self.assertEqual(state['exit_status'], 0, (root / 'result.next/work/full-build-attempts/001/full-build.log').read_text())
            self.assertTrue(module.publish_verified_result(context, '001'))
            results = root / 'result/work/results'
            self.assertEqual(read_json(results / 'deployment.json')['state'], 'complete')
            # A new SSH call cannot start a second execution after completion.
            self.assertEqual(call('_remote-worker', '--attempt', '001')['exit_status'], 0)
        else:
            self.assertNotEqual(state['exit_status'], 0)
            results = root / 'result.next/work/results'
        return results

    def fixture_package(self, name, changes=None, seconds=180, through='report'):
        root = Path(os.environ['DISTILLATION_DEPLOY_OUTPUT']) / name
        root.mkdir(parents=True)
        config = read_json(Path(os.environ['DISTILLATION_TEST_OUTPUT']) / 'config.json')
        config.update(changes or {})
        if 'training_milestones' in config:
            from sse_multivector import distillation_data
            source = Path(os.environ['DISTILLATION_TEST_OUTPUT'])
            distillation_data.prepare(source / 'source.json', source / 'annotations.json', source / 'subjects.txt',
                None, 'AS-test', None, 2, 'test', root / 'subject-data', tasks=('subjects',))
            config['data'] = str(root / 'subject-data')
            for key in ('mask_prompt', 'mask_batch_size', 'subject_fraction', 'max_steps', 'save_steps'):
                config.pop(key)
            config['max_new_tokens'] = {'subjects': config['max_new_tokens']['subjects']}
        paths = []
        for candidate in ('first', 'second'):
            path = root / (candidate + '.json')
            write_json(path, config)
            paths.append(path)
        deploy.prepare(paths, root / 'inputs', seconds, through=through)
        return root

    def test_two_candidates_train_and_retrieve_through_shared_ssh(self):
        root = self.fixture_package('training')
        result = self.run_package(root / 'inputs', root / 'operation')
        for name in ('first', 'second'):
            self.assertTrue(read_json(result / name / 'report.json')['training']['reload_matches'])

    def test_dynamic_subject_batches_train_and_retrieve_through_shared_ssh(self):
        policy = {'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                  'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4}
        root = self.fixture_package('dynamic-subjects', {
            'evaluation_tasks': ['subjects'], 'subject_batching': policy})
        result = self.run_package(root / 'inputs', root / 'operation')
        for name in ('first', 'second'):
            run = result / name
            self.assertEqual(read_json(run / 'manifest.json')['config']['subject_batching'], policy)
            for stage in ('baseline', 'trained'):
                self.assertEqual(read_json(run / stage / 'subject-batches.json')['policy'], policy)
                receipt = read_json(run / stage / 'subjects-0000.json')
                self.assertEqual(len(receipt['answers']), len(receipt['note_ids']))
                self.assertEqual(len(list((run / stage).glob('note-*/subjects-result.json'))), len(receipt['note_ids']))
                self.assertFalse(list((run / stage).glob('note-*/masks-*.json')))

    def test_subject_pilot_checkpoints_and_answers_retrieve_through_shared_ssh(self):
        policy = {'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                  'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4}
        root = self.fixture_package('subject-pilot', {'training_milestones': [1, 2, 3, 4, 6],
            'batch_size': 1, 'gradient_accumulation_steps': 8,
            'evaluation_tasks': ['subjects'], 'subject_batching': policy})
        result = self.run_package(root / 'inputs', root / 'operation')
        from sse_multivector.distillation_run import verify_saved
        for name in ('first', 'second'):
            run = result / name
            report = read_json(run / 'report.json')
            self.assertEqual(report['training'], {'examples': 6, 'updates': 5})
            self.assertEqual(len(report['checkpoints']), 5)
            for milestone in (1, 2, 3, 4, 6):
                self.assertTrue(verify_saved(run / f'checkpoints/checkpoint-{milestone}'))
                self.assertTrue(verify_saved(run / f'evaluations/checkpoint-{milestone}'))

    def test_subject_preparation_retrieves_all_checks_without_baseline(self):
        from sse_multivector.distillation_run import load_data, verify_saved
        source = Path(os.environ['DISTILLATION_TEST_OUTPUT'])
        data = load_data(source / 'data', source / 'masks.txt')
        training_ids = list(dict.fromkeys(row['note_id'] for row in data['train']))
        evaluation_ids = [row['note_id'] for row in data['evaluation']]
        root = self.fixture_package('subject-preparation', {
            'training_milestones': [3, 6], 'batch_size': 1, 'gradient_accumulation_steps': 8,
            'evaluation_tasks': ['subjects'],
            'subject_batching': {'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                                'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4},
            'preparation': {'max_new_tokens': 4, 'cache_fill_tokens': 16,
                            'train_note_ids': training_ids, 'evaluation_note_ids': evaluation_ids}},
            through='preparation', seconds=None)
        result = self.run_package(root / 'inputs', root / 'operation')
        self.assertIsNone(read_json(result / 'deployment.json')['deadline'])
        for name in ('first', 'second'):
            run = result / name
            self.assertEqual(read_json(run / 'report.json')['training'], {'examples': 6, 'updates': 2})
            self.assertTrue(verify_saved(run / 'preparation'))
            self.assertEqual(len(list((run / 'preparation').glob('note-*/subjects.json'))), 2)
            for milestone in (3, 6):
                self.assertTrue(verify_saved(run / f'checkpoints/checkpoint-{milestone}'))
            self.assertFalse((run / 'baseline').exists())
            self.assertFalse((run / 'evaluations').exists())

    def test_subject_responses_and_checkpoints_copy_while_training_is_running(self):
        policy = {'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                  'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4}
        root = self.fixture_package('progressive-subject-pilot', {'training_milestones': [1, 2, 3, 4, 6],
            'batch_size': 1, 'gradient_accumulation_steps': 8,
            'evaluation_tasks': ['subjects'], 'subject_batching': policy})
        result = self.run_package(root / 'inputs', root / 'operation', copy_while_running=True)
        from sse_multivector.distillation_run import verify_saved
        for candidate in ('first', 'second'):
            self.assertTrue(verify_saved(result / candidate / 'baseline'))
            for milestone in (1, 2, 3, 4, 6):
                self.assertTrue(verify_saved(result / candidate / f'checkpoints/checkpoint-{milestone}'))
                self.assertTrue(verify_saved(result / candidate / f'evaluations/checkpoint-{milestone}'))

    def test_failure_preserves_logs(self):
        root = self.fixture_package('failure', {'max_length': 8})
        result = self.run_package(root / 'inputs', root / 'operation', expected=1)
        self.assertEqual(read_json(result / 'deployment.json')['state'], 'failed')
        self.assertIn('invalid sampling, learning rate or length', (result / 'first.log').read_text())
        self.assertFalse((result / 'second.log').exists())

    def test_worker_deadline_preserves_failure(self):
        root = self.fixture_package('deadline', {'max_steps': 1000000}, seconds=1)
        result = self.run_package(root / 'inputs', root / 'operation', expected=1)
        state = read_json(result / 'deployment.json')
        self.assertEqual(state['state'], 'failed')
        self.assertLess(state['finished'] - state['deadline'], 10)

    def test_stop_preserves_partial_results(self):
        root = self.fixture_package('stop', {'max_steps': 1000000})
        result = self.run_package(root / 'inputs', root / 'operation', expected=1, stop=True)
        self.assertEqual(read_json(result / 'deployment.json')['state'], 'failed')

    def test_actual_candidate_preflights(self):
        inputs = Path(os.environ.get('DISTILLATION_PREFLIGHT_PACKAGE', '/missing'))
        if not inputs.is_dir():
            self.skipTest('no frozen candidate tokenizer package supplied')
        self.run_package(inputs, Path(os.environ['DISTILLATION_DEPLOY_OUTPUT']) / 'candidate-preflight')
