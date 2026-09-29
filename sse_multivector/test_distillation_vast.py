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
            self.assertIs(spec['ssh_direct'], True)
            self.assertEqual(spec['limits']['maximum_charge_cents'], 2500)
            self.assertEqual(spec['limits']['work_seconds'], 43200)
            self.assertEqual(spec['limits']['session_seconds'], 50400)
            self.assertEqual(spec['limits']['cleanup_seconds'], 900)
            self.assertEqual(spec['command'][0], deploy.REMOTE_PYTHON)
            self.assertEqual(spec['outputs'], ['results'])
            self.assertIn('/usr/local/cuda/bin', spec['environment']['PATH'].split(':'))
            self.assertIn('/usr/local/nvidia/bin', spec['environment']['PATH'].split(':'))
            self.assertEqual(deploy.verify_package(inputs)['through'], 'report')
            with self.assertRaisesRegex(ValueError, 'digest'):
                vast.make_spec(settings, offer, inputs, 'mutable:latest')
            with self.assertRaisesRegex(ValueError, 'gpu_ram'):
                vast.make_spec(settings, {**offer, 'gpu_ram': 48000}, inputs, image)


if __name__ == '__main__':
    unittest.main()
