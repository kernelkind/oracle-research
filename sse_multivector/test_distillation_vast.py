"""Distillation uses the shared command workload, without provider calls."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_deploy as deploy
from sse_multivector import distillation_vast as vast
from sse_multivector.distillation_run import read_json, write_json
from sse_multivector.test_distillation_data import DistillationDataTests


def quote():
    settings = read_json(Path(__file__).parent / 'distillation/vast-launch.json')
    return settings, {**settings['offer_equals'], **settings['offer_minimums'],
        **settings['offer_maximums'], 'id': 123, 'machine_id': 12, 'bundle_id': 23,
        'driver_version': '595.58.03', 'dph_base': 1.5, 'storage_cost': .24,
        'storage_total_cost': .1}


class WorkloadTests(unittest.TestCase):
    def test_two_gpu_package_rejects_a_one_gpu_offer(self):
        settings, offer = quote()
        settings['worker_timeout_seconds'] = None
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            paths = []
            for name in ('first', 'second'):
                path = root / (name + '.json')
                write_json(path, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                                 'model': 'example/model', 'revision': 'a'*40})
                paths.append(path)
            inputs = root / 'inputs'
            deploy.prepare(paths, inputs, through='preflight', gpu_assignments={'first': 0, 'second': 1})
            image = settings['image_repository'] + '@sha256:' + '4'*64
            with self.assertRaisesRegex(ValueError, 'requires 2 GPUs'):
                vast.make_spec(settings, offer, inputs, image)
            settings['offer_equals']['num_gpus'] = offer['num_gpus'] = 2
            spec = vast.make_spec(settings, offer, inputs, image)
            self.assertEqual(spec['offer']['num_gpus'], 2)

    def test_launch_settings_select_proxy_and_preserve_explicit_direct_override(self):
        settings, offer = quote()
        with self.subTest(default='proxy'):
            self.assertIs(settings['ssh_direct'], False)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                'model': 'example/model', 'revision': 'a' * 40})
            deploy.prepare([config], root / 'inputs', 43200)
            image = settings['image_repository'] + '@sha256:' + '4' * 64
            for direct in (False, True):
                settings['ssh_direct'] = direct
                with self.subTest(ssh_direct=direct):
                    self.assertIs(vast.make_spec(settings, offer, root / 'inputs', image)['ssh_direct'], direct)

    def test_unbounded_preparation_has_no_worker_deadline(self):
        sys.path.insert(0, str(deploy.CODE_ROOT / 'vast'))
        import package as packager
        settings, offer = quote()
        settings['worker_timeout_seconds'] = None
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                'model': 'example/model', 'revision': 'a' * 40})
            deploy.prepare([config], root / 'inputs', None, through='preparation')
            spec = vast.make_spec(settings, offer, root / 'inputs',
                                  settings['image_repository'] + '@sha256:' + '4' * 64)
            ledger = root / 'ledger.json'
            write_json(ledger, {'lifetime_cap_cents': 100000, 'actual_spend_cents': 0,
                'outstanding_commitments_cents': 0, 'reserved_remaining_work_cents': 0, 'entries': []})
            contract = read_json(packager.freeze(spec, root / 'operation', ledger))
            self.assertIsNone(contract['workload']['work_seconds'])
            self.assertIsNone(deploy.verify_package(root / 'inputs')['timeout_seconds'])

    def test_small_preparation_budget_freezes_in_shared_controller(self):
        sys.path.insert(0, str(deploy.CODE_ROOT / 'vast'))
        import package as packager
        settings, offer = quote()
        settings.update(approved_maximum_usd=5, rental_hours=3,
                        worker_timeout_seconds=9000,
                        setup_cost_cents=100, manual_stop_cost_cents=475)
        settings['offer_maximums'] = {**settings['offer_maximums'],
            'inet_down_cost': .0001, 'inet_up_cost': .0001}
        offer.update(inet_down_cost=.0001, inet_up_cost=.0001)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                'model': 'example/model', 'revision': 'a' * 40})
            deploy.prepare([config], root / 'inputs', 9000, through='preparation')
            spec = vast.make_spec(settings, offer, root / 'inputs',
                                  settings['image_repository'] + '@sha256:' + '4' * 64)
            ledger = root / 'ledger.json'
            write_json(ledger, {'lifetime_cap_cents': 100000, 'actual_spend_cents': 0,
                'outstanding_commitments_cents': 0, 'reserved_remaining_work_cents': 0, 'entries': []})
            contract = read_json(packager.freeze(spec, root / 'operation', ledger))
            self.assertEqual(contract['limits']['reservation_ceiling_micro_usd'], 5_000_000)
            self.assertEqual(contract['limits']['setup_cost_micro_usd'], 1_000_000)
            self.assertEqual(contract['limits']['manual_stop_cost_micro_usd'], 4_750_000)

    def test_freezes_shared_workload_with_preserved_experiment_and_budget(self):
        settings, offer = quote()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                'model': 'example/model', 'revision': 'a' * 40})
            inputs = root / 'inputs'
            deploy.prepare([config], inputs, 43200)
            image = settings['image_repository'] + '@sha256:' + '4' * 64
            spec = vast.make_spec(settings, offer, inputs, image)
            self.assertEqual(spec['offer'], offer)
            self.assertEqual(spec['onstart'], 'ssh-keygen -A && service ssh start')
            self.assertIs(spec['ssh_direct'], False)
            self.assertEqual(spec['limits']['maximum_charge_cents'], 2500)
            self.assertEqual(spec['limits']['work_seconds'], 43200)
            self.assertEqual(spec['limits']['session_seconds'], 50400)
            self.assertEqual(spec['limits']['cleanup_seconds'], 900)
            self.assertEqual(spec['command'][0], deploy.REMOTE_PYTHON)
            self.assertEqual(spec['outputs'], ['results'])
            self.assertEqual(spec['progressive_copy'], {'poll_seconds': 5, 'bytes_per_second': 8 * 1024 * 1024,
                                                        'timeout_seconds': 900})
            self.assertIn('/usr/local/cuda/bin', spec['environment']['PATH'].split(':'))
            self.assertIn('/usr/local/nvidia/bin', spec['environment']['PATH'].split(':'))
            self.assertEqual(deploy.verify_package(inputs)['through'], 'report')
            with self.assertRaisesRegex(ValueError, 'digest'):
                vast.make_spec(settings, offer, inputs, 'mutable:latest')
            with self.assertRaisesRegex(ValueError, 'gpu_ram'):
                vast.make_spec(settings, {**offer, 'gpu_ram': 48000}, inputs, image)


if __name__ == '__main__':
    unittest.main()
