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
    def run_package(self, inputs, root, expected=0, stop=False):
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
        spec = make_spec(settings, offer, inputs, settings['image_repository'] + '@sha256:' + '4' * 64)
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
        if stop:
            time.sleep(2)
            call('_remote-stop', '--attempt', '001')
        while True:
            state = call('_remote-status', '--attempt', '001')
            if state['state'] == 'terminal':
                break
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.5)
        (root / 'result.next').mkdir()
        module.ensure_retrieved(context, 'offline-fixture', key, endpoint, '001')
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

    def fixture_package(self, name, changes=None, seconds=180):
        root = Path(os.environ['DISTILLATION_DEPLOY_OUTPUT']) / name
        root.mkdir(parents=True)
        config = read_json(Path(os.environ['DISTILLATION_TEST_OUTPUT']) / 'config.json')
        config.update(changes or {})
        paths = []
        for candidate in ('first', 'second'):
            path = root / (candidate + '.json')
            write_json(path, config)
            paths.append(path)
        deploy.prepare(paths, root / 'inputs', seconds)
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
