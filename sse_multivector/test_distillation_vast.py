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
    def test_one_gpu_download_workload_requires_volume_and_no_training(self):
        from gte.full_build_package import write_manifest
        settings, offer = quote()
        settings['offer_equals']['num_gpus'] = offer['num_gpus'] = 1
        settings['worker_timeout_seconds'] = None
        settings['local_volume'] = {'id': 881, 'machine_id': offer['machine_id']}
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary)
            write_json(package / 'model-cache.json', {'version': 1, 'reserve_bytes': 0, 'models': [{
                'model': 'fixture/cached', 'revision': 'a'*40, 'files': [{
                    'path': 'config.json', 'size': 2, 'git_blob_sha1': 'b'*40}]}]})
            write_json(package / 'job.json', {'cache_manifest': 'model-cache.json',
                'timeout_seconds': None, 'code': deploy.code_hashes()})
            write_manifest(package, package / 'manifest.json', 'distillation-model-cache')
            image = settings['image_repository'] + '@sha256:' + '4'*64
            spec = vast.make_cache_spec(settings, offer, package, image)
            self.assertIn('sse_multivector.distillation_cache', spec['command'])
            self.assertIn('download', spec['command'])
            self.assertNotIn('distillation_deploy', spec['command'])
            self.assertTrue(spec['resumable'])
            self.assertIsNone(spec['limits']['work_seconds'])
            self.assertEqual(spec['environment']['HF_HOME'], '/workspace/oracle-full-build/model-cache')
            del settings['local_volume']
            with self.assertRaisesRegex(ValueError, 'requires a local volume'):
                vast.make_cache_spec(settings, offer, package, image)

    def test_volume_replacement_verifies_work_and_archives_old_launch_receipts(self):
        import argparse
        import importlib.util
        import shutil
        sys.path.insert(0, str(deploy.CODE_ROOT / 'vast'))
        import package as packager
        from vast import runner
        settings, offer = quote()
        settings['local_volume'] = {'id': 881, 'machine_id': offer['machine_id']}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                'model': 'example/model', 'revision': 'a'*40, 'training_milestones': [1, 2]})
            deploy.prepare([config], root / 'inputs', 43200)
            spec = vast.make_spec(settings, offer, root / 'inputs',
                                 settings['image_repository'] + '@sha256:' + '4'*64)
            ledger = root / 'ledger.json'
            write_json(ledger, {'lifetime_cap_cents': 100000, 'actual_spend_cents': 0,
                'outstanding_commitments_cents': 0, 'reserved_remaining_work_cents': 0, 'entries': []})
            old = root / 'old'
            old_config = packager.freeze(spec, old, ledger)
            volume = root / 'volume'
            volume.mkdir()
            shutil.copytree(old / 'transport', volume / 'transport')
            (volume / 'launch').mkdir(exist_ok=True)
            shutil.copy2(old_config, volume / 'launch/operation-contract.json')
            (volume / 'work/full-build-attempts/001').mkdir(parents=True)
            (volume / 'work/full-build-attempts/001/full-build.exit').write_text('1\n')
            (volume / 'work/checkpoint.bin').write_bytes(b'checkpoint')
            (volume / 'work/full-build-start.lock').touch()
            (volume / 'work/full-build.lock').touch()
            (volume / 'model-cache').mkdir()
            (volume / 'model-cache/download.bin').write_bytes(b'cached weights')
            records = runner.tree_file_records(volume / 'work', {'retrieval-manifest.json'})
            write_json(volume / 'work/retrieval-manifest.json', {'files': records})
            shutil.copytree(volume / 'work', old / 'result.next/work')
            write_json(old / 'launch/retrieval-verification.json', {'instance_id': '42', 'attempt_id': '001', 'work_files': records})
            write_json(old / 'launch/destruction-confirmation.json', {'instance_id': '42',
                'absent_from_complete_inventory': True, 'absence_observations': 2})
            spec['recover_from'] = str(old)
            spec['label'] += '-replacement'
            staging = volume / 'replacements/new'
            new_config = packager.freeze(spec, staging, ledger)
            self.assertEqual(read_json(new_config)['volume_recovery']['previous_attempt'], '001')
            (staging / 'launch').mkdir()
            shutil.copy2(new_config, staging / 'launch/operation-contract.json')
            definition = importlib.util.spec_from_file_location('volume_runner', staging / 'transport/control/vast_full_build.py')
            module = importlib.util.module_from_spec(definition)
            sys.modules[definition.name] = module
            definition.loader.exec_module(module)
            context = module.Context.load(argparse.Namespace(root=staging, config=new_config, operation='_remote-volume-prepare'))
            with patch.object(module, 'completed_process'), \
                    module.file_lock(volume / 'work/full-build.lock', blocking=False):
                with self.assertRaisesRegex(Exception, 'lock'):
                    module.remote_volume_prepare(context, volume)
            (volume / 'work/checkpoint.bin').write_bytes(b'bad')
            with patch.object(module, 'completed_process'), self.assertRaisesRegex(Exception, 'integrity'):
                module.remote_volume_prepare(context, volume)
            (volume / 'work/checkpoint.bin').write_bytes(b'checkpoint')
            rename = module.os.rename
            def interrupted(source, destination):
                if Path(source).name == 'transport':
                    raise OSError('interrupted replacement')
                return rename(source, destination)
            with patch.object(module, 'completed_process'), patch.object(module.os, 'rename', side_effect=interrupted):
                with self.assertRaisesRegex(OSError, 'interrupted replacement'):
                    module.remote_volume_prepare(context, volume)
            with patch.object(module, 'completed_process') as mount:
                result = module.remote_volume_prepare(context, volume)
                self.assertTrue(result['recovered'])
                mount.assert_called_once_with(['mountpoint', '-q', str(volume)])
                self.assertEqual(module.remote_volume_prepare(context, volume), result)
            self.assertEqual((volume / 'work/checkpoint.bin').read_bytes(), b'checkpoint')
            self.assertEqual((volume / 'model-cache/download.bin').read_bytes(), b'cached weights')
            self.assertFalse((volume / 'launch/operation-contract.json').exists())
            self.assertEqual((volume / 'work/full-build-attempts/001/full-build.exit').read_text(), '1\n')
            archive = volume / result['archive']
            self.assertEqual(read_json(archive / 'launch/operation-contract.json'), read_json(old_config))
            changed = {**spec, 'image': settings['image_repository'] + '@sha256:' + '5'*64}
            with self.assertRaisesRegex(Exception, 'same volume, image and frozen workload'):
                packager.freeze(changed, root / 'changed', ledger)
            changed.update(reuse_work=False, recovery_reason='Rebuild after a runtime repair; retain downloads only')
            cached = root / 'cache-only-volume'
            cached.mkdir()
            (cached / 'launch').mkdir()
            shutil.copy2(old_config, cached / 'launch/operation-contract.json')
            shutil.copytree(old / 'result.next/work', cached / 'work')
            shutil.copytree(volume / 'model-cache', cached / 'model-cache')
            cache_staging = cached / 'replacements/new-runtime'
            cache_config = packager.freeze(changed, cache_staging, ledger)
            self.assertFalse(read_json(cache_config)['volume_recovery']['reuse_work'])
            definition = importlib.util.spec_from_file_location('cache_volume_runner', cache_staging / 'transport/control/vast_full_build.py')
            cache_module = importlib.util.module_from_spec(definition)
            sys.modules[definition.name] = cache_module
            definition.loader.exec_module(cache_module)
            cache_context = cache_module.Context.load(argparse.Namespace(root=cache_staging, config=cache_config,
                                                                          operation='_remote-volume-prepare'))
            with patch.object(cache_module, 'completed_process'):
                reset = cache_module.remote_volume_prepare(cache_context, cached)
            self.assertFalse(reset['reused_work'])
            self.assertFalse((cached / 'work').exists())
            self.assertEqual((cached / reset['archive'] / 'work/checkpoint.bin').read_bytes(), b'checkpoint')
            self.assertEqual((cached / 'model-cache/download.bin').read_bytes(), b'cached weights')
            # A damaged local source cannot become a replacement approval.
            (old / 'result.next/work/checkpoint.bin').write_bytes(b'bad')
            with self.assertRaisesRegex(Exception, 'integrity'):
                packager.freeze(spec, root / 'rejected', ledger)

    def test_volume_spec_binds_the_host_and_keeps_model_downloads(self):
        settings, offer = quote()
        settings['local_volume'] = {'id': 881, 'machine_id': offer['machine_id']}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            config = root / 'candidate.json'
            write_json(config, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                'model': 'example/model', 'revision': 'a'*40})
            deploy.prepare([config], root / 'inputs', 43200)
            image = settings['image_repository'] + '@sha256:' + '4'*64
            spec = vast.make_spec(settings, offer, root / 'inputs', image)
            self.assertEqual(spec['local_volume'], settings['local_volume'])
            self.assertEqual(spec['environment']['HF_HOME'], '/workspace/oracle-full-build/model-cache')
            settings['local_volume']['machine_id'] += 1
            with self.assertRaisesRegex(ValueError, 'machine'):
                vast.make_spec(settings, offer, root / 'inputs', image)

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
