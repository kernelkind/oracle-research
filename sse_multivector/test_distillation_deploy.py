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
    def test_supervisor_identifies_the_lock_descriptor_inherited_by_the_controller(self):
        from vast import runner
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = runner.Context(root, root / 'contract.json', root / 'ledger.json', {})
            attempt = context.path('work/full-build-attempts/001')
            attempt.mkdir(parents=True)
            (attempt / 'controller.pid').write_text('42\n')
            (attempt / 'full-build.started').write_text('started\n')
            preparation = context.path('preparation-attempts/001/preparation.exit')
            preparation.parent.mkdir(parents=True)
            preparation.write_text('0\n')
            def child(*args, **kwargs):
                fd, = kwargs['pass_fds']
                self.assertEqual(kwargs['env']['ORACLE_RUN_WORKER_LOCK_FD'], str(fd))
                self.assertEqual(os.fstat(fd).st_ino, (root / 'work/full-build.lock').stat().st_ino)
                return type('Process', (), {'wait': lambda self: 0})()
            with runner.file_lock(root / 'work/full-build-start.lock', blocking=False) as lock, \
                    patch.object(runner.subprocess, 'Popen', side_effect=child):
                result = runner.remote_supervise(context, '001', os.dup(lock.fileno()))
            self.assertEqual(result['exit_status'], 0)

    def test_controller_crash_keeps_live_child_unsealed_until_it_finishes(self):
        import ctypes
        import signal
        import time
        from vast import runner
        libc = ctypes.CDLL(None, use_errno=True)
        previous = ctypes.c_int()
        self.assertEqual(libc.prctl(37, ctypes.byref(previous), 0, 0, 0), 0)
        self.assertEqual(libc.prctl(36, 1, 0, 0, 0), 0)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = {'artifact_kind': 'vast-command-operation', 'workload': {'work_seconds': None}}
            context = runner.Context(root, root / 'contract.json', root / 'ledger.json', config)
            attempt = context.path('work/full-build-attempts/001')
            attempt.mkdir(parents=True)
            context.path('preparation-attempts').mkdir()
            context.path('preparation-attempts/preparation.exit').write_text('0\n')
            child = '''import os,time
from pathlib import Path
from vast import runner
root=Path(%r)
runner.atomic_bytes(root/'child.pid',f'{os.getpid()}\\n'.encode())
while not (root/'finish').exists():
    runner.atomic_json(root/'work/heartbeat.json',{'updated':time.time_ns()},replace=True)
    time.sleep(.02)
''' % str(root)
            parent = '''import os,sys
from pathlib import Path
from vast import runner
from sse_multivector.distillation_deploy import run_process
root=Path(%r)
with runner.file_lock(root/'work/full-build.lock',blocking=False) as lock:
    os.environ['ORACLE_RUN_WORKER_LOCK_FD']=str(lock.fileno())
    runner.atomic_bytes(root/'work/full-build-attempts/001/controller.pid',f'{os.getpid()}\\n'.encode())
    runner.atomic_bytes(root/'work/full-build-attempts/001/full-build.started',b'started\\n')
    run_process([sys.executable,'-B','-c',%r],None)
''' % (str(root), child)
            process = subprocess.Popen([sys.executable, '-B', '-c', parent],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            pid = None
            try:
                deadline = time.monotonic() + 10
                while not (root / 'child.pid').exists() and process.poll() is None:
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
                pid = int((root / 'child.pid').read_text())
                process.kill()
                process.communicate(timeout=5)
                # A surviving child also protects against a terminal exit receipt
                # published by the supervisor after the controller's death.
                for terminal in (False, True):
                    if terminal:
                        runner.atomic_bytes(attempt / 'full-build.exit', b'137\n')
                    self.assertEqual(runner.remote_attempt_status(context, '001')['state'], 'running')
                    with self.assertRaisesRegex(runner.OperationError, 'lock'):
                        runner.remote_seal(context, '001')
                    self.assertFalse(context.path('work/retrieval-manifest.json').exists())
                (root / 'finish').touch()
                os.waitpid(pid, 0)
                pid = None
                self.assertEqual(runner.remote_attempt_status(context, '001')['state'], 'terminal')
                sealed = runner.remote_seal(context, '001')
                self.assertTrue(sealed['terminal'])
                record = next(r for r in sealed['work_files'] if r['path'] == 'heartbeat.json')
                self.assertEqual(runner.sha256_file(root / 'work/heartbeat.json'), record['sha256'])
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=5)
                if pid is not None:
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    os.waitpid(pid, 0)
                libc.prctl(36, previous.value, 0, 0, 0)

    def test_tokenizer_preflight_needs_no_cuda_but_gpu_work_requires_two_devices(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            paths = []
            for name in ('first', 'second'):
                path = root / (name + '.json')
                write_json(path, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                                 'model': 'org/model', 'revision': 'a'*40, 'device': 'cuda'})
                paths.append(path)
            for mode, count in [('preflight', 0), ('baseline', 1)]:
                package = root / mode
                deploy.prepare(paths, package, through=mode, gpu_assignments={'first': 0, 'second': 1})
                torch = SimpleNamespace(cuda=SimpleNamespace(device_count=lambda: count))
                with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {'torch': torch}), \
                        patch.object(deploy, 'run_process', return_value=subprocess.CompletedProcess([], 0)) as child:
                    if mode == 'preflight':
                        self.assertEqual(deploy.execute(package, root / 'preflight-results')['state'], 'complete')
                        self.assertEqual(child.call_count, 2)
                    else:
                        with self.assertRaisesRegex(ValueError, 'visible CUDA devices'):
                            deploy.execute(package, root / 'baseline-results')
                        child.assert_not_called()

    def test_parallel_failure_preserves_the_other_active_candidate_and_blocks_queued_work(self):
        import threading
        import time
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            assignments = {'first': 0, 'second': 1, 'third': 0}
            paths = []
            for name in assignments:
                path = root / (name + '.json')
                write_json(path, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                                 'model': 'org/model', 'revision': 'a'*40, 'device': 'cpu'})
                paths.append(path)
            package, output = root / 'package', root / 'results'
            deploy.prepare(paths, package, through='preflight', gpu_assignments=assignments)
            started, calls = threading.Barrier(2), []
            def child(command, **kwargs):
                name = Path(command[3]).stem
                calls.append(name)
                started.wait(timeout=5)
                if name == 'first':
                    (output / 'first-evidence').write_text('preserved failed work')
                    return type('Result', (), {'returncode': 7})()
                deadline = time.monotonic() + 5
                while 'failures' not in read_json(output / 'deployment.json'):
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
                (output / 'second-evidence').write_text('active candidate finished')
                return type('Result', (), {'returncode': 0})()
            with patch.dict(os.environ, {}, clear=True), patch.object(deploy, 'run_process', side_effect=child):
                with self.assertRaisesRegex(RuntimeError, 'first failed with exit code 7'):
                    deploy.execute(package, output)
            self.assertEqual(set(calls), {'first', 'second'})
            self.assertTrue((output / 'first-evidence').is_file())
            self.assertTrue((output / 'second-evidence').is_file())
            self.assertEqual(read_json(output / 'deployment.json')['active_runs'], {})

    def test_two_gpu_children_follow_explicit_stop_and_continue_after_interrupt(self):
        import json
        import signal
        import time
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            paths = []
            for name in ('first', 'second'):
                path = root / (name + '.json')
                write_json(path, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                                 'model': 'org/model', 'revision': 'a'*40, 'device': 'cpu'})
                paths.append(path)
            package = root / 'package'
            deploy.prepare(paths, package, through='preflight', gpu_assignments={'first': 0, 'second': 1})
            for operation, signum, pause in [('stop', signal.SIGTERM, 60), ('interrupt', signal.SIGINT, .7)]:
                with self.subTest(operation=operation):
                    output = root / operation
                    script = f'''import sys
from pathlib import Path
from sse_multivector import distillation_deploy as deploy
real = deploy.run_process
def child(command, timeout, **kwargs):
    name = Path(command[3]).stem
    ready = Path({str(output)!r}) / (name + '-ready.json')
    done = Path({str(output)!r}) / (name + '-done')
    code = ('import json,os,sys,time; from pathlib import Path; '
            'Path(sys.argv[1]).write_text(json.dumps({{"pid":os.getpid(),"gpu":os.environ.get("CUDA_VISIBLE_DEVICES")}})); '
            'time.sleep(float(sys.argv[3])); Path(sys.argv[2]).touch()')
    return real([sys.executable, '-B', '-c', code, str(ready), str(done), '{pause}'], timeout, **kwargs)
deploy.run_process = child
deploy.execute(Path({str(package)!r}), Path({str(output)!r}))
'''
                    env = {k: v for k, v in os.environ.items() if k != 'CUDA_VISIBLE_DEVICES'}
                    process = subprocess.Popen([sys.executable, '-B', '-c', script], env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                    pids = []
                    try:
                        deadline = time.monotonic() + 10
                        while time.monotonic() < deadline and process.poll() is None:
                            if all((output / (name + '-ready.json')).exists() for name in ('first', 'second')):
                                break
                            time.sleep(.01)
                        records = [json.loads((output / (name + '-ready.json')).read_text()) for name in ('first', 'second')]
                        pids = [r['pid'] for r in records]
                        self.assertEqual([r['gpu'] for r in records], ['0', '1'])
                        process.send_signal(signum)
                        stdout, stderr = process.communicate(timeout=10)
                        state = read_json(output / 'deployment.json')
                        self.assertEqual(state['active_runs'], {})
                        if operation == 'stop':
                            self.assertNotEqual(process.returncode, 0)
                            self.assertEqual(state['state'], 'failed')
                            self.assertFalse(any((output / (name + '-done')).exists() for name in ('first', 'second')))
                        else:
                            self.assertEqual(process.returncode, 0, stderr.decode())
                            self.assertEqual(state['state'], 'complete')
                            self.assertTrue(all((output / (name + '-done')).exists() for name in ('first', 'second')))
                            self.assertIn(b'unbounded job continues', stderr)
                        for pid in pids:
                            with self.assertRaises(ProcessLookupError):
                                os.kill(pid, 0)
                    finally:
                        if process.poll() is None:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        for path in output.glob('*-ready.json'):
                            try:
                                os.killpg(json.loads(path.read_text())['pid'], signal.SIGKILL)
                            except ProcessLookupError:
                                pass

    def test_gpu_assignment_validation_and_inherited_mask_fail_before_starting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            paths = []
            for name in ('first', 'second'):
                path = root / (name + '.json')
                write_json(path, {'data': str(root / 'prepared'), 'mask_prompt': str(root / 'masks.txt'),
                                 'model': 'org/model', 'revision': 'a'*40, 'device': 'cpu'})
                paths.append(path)
            for index, assignments in enumerate(({}, {'first': 0}, {'first': 0, 'other': 1},
                    {'first': True, 'second': 0}, {'first': -1, 'second': 0}, {'first': 0, 'second': 2})):
                with self.subTest(assignments=assignments), self.assertRaisesRegex(ValueError, 'GPU assignments'):
                    deploy.prepare(paths, root / f'invalid-{index}', through='preflight', gpu_assignments=assignments)
                self.assertFalse((root / f'invalid-{index}').exists())
            package, output = root / 'package', root / 'results'
            deploy.prepare(paths, package, through='preflight', gpu_assignments={'first': 0, 'second': 1})
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'GPU-A'}), \
                    patch.object(deploy, 'run_process') as child:
                with self.assertRaisesRegex(ValueError, 'inherited CUDA_VISIBLE_DEVICES'):
                    deploy.execute(package, output)
                child.assert_not_called()
            self.assertEqual(read_json(output / 'deployment.json')['state'], 'failed')

    def test_gpu_assignments_run_two_lanes_with_global_baseline_gate(self):
        import threading
        from sse_multivector import distillation_data
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            data = root / 'subjects'
            manifest = distillation_data.prepare(root / 'source.json', root / 'annotations.json',
                root / 'subjects.txt', None, 'AS-test', None, 2, 'pilot', data, tasks=('subjects',))
            configs, preparations = [], []
            assignments = {'first': 1, 'second': 0, 'third': 1}
            for name in assignments:
                config, prep = root / (name + '.json'), root / 'prep' / (name + '.json')
                recipe = {'data': str(data), 'model': 'org/model', 'revision': 'a'*40,
                          'device': 'cpu', 'training_milestones': [2, 4], 'evaluation_tasks': ['subjects'],
                          'max_new_tokens': {'subjects': 8}}
                write_json(config, recipe)
                write_json(prep, {**recipe, 'training_milestones': [1, 2], 'preparation': {
                    'train_note_ids': manifest['train_note_ids'][:2],
                    'evaluation_note_ids': manifest['evaluation_note_ids'][:1],
                    'max_new_tokens': 4, 'cache_fill_tokens': 16}})
                configs.append(config)
                preparations.append(prep)
            package, output = root / 'package', root / 'results'
            deploy.prepare(configs, package, preparation_configs=preparations, gpu_assignments=assignments)
            self.assertEqual(deploy.verify_package(package)['gpu_assignments'], assignments)
            lock, active, calls, prepared, baselines = threading.Lock(), set(), [], set(), set()
            rendezvous = {mode: threading.Barrier(2) for mode in ('preparation', 'baseline', 'report')}
            def child(command, **kwargs):
                name, mode = Path(command[3]).stem, command[-1]
                gpu = kwargs['env']['CUDA_VISIBLE_DEVICES']
                with lock:
                    self.assertNotIn(gpu, active)
                    active.add(gpu)
                    calls.append((name, mode, gpu))
                    if mode == 'baseline':
                        self.assertEqual(prepared, set(assignments))
                    elif mode == 'report':
                        self.assertEqual(baselines, set(assignments))
                    live = read_json(output / 'deployment.json')['active_runs']
                    self.assertEqual(live[name]['gpu'], assignments[name])
                if name != 'third':
                    rendezvous[mode].wait(timeout=5)
                with lock:
                    active.remove(gpu)
                return type('Result', (), {'returncode': 0})()
            def verify(directory, *args):
                with lock:
                    if directory.parent.name == 'preparation':
                        prepared.add(directory.name)
                return {'status': 'complete'}
            def baseline(directory, *args):
                with lock:
                    baselines.add(directory.parent.name)
                return {'notes': 2}
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': 'GPU-A,GPU-B'}), \
                    patch.object(deploy, 'run_process', side_effect=child), \
                    patch.object(deploy, 'verify_subject_run', side_effect=verify), \
                    patch.object(deploy, 'subject_stage_summary', side_effect=baseline):
                self.assertEqual(deploy.execute(package, output)['state'], 'complete')
            self.assertEqual(len(calls), 9)
            for name, mode, gpu in calls:
                self.assertEqual(gpu, 'GPU-A' if assignments[name] == 0 else 'GPU-B')
            self.assertEqual(read_json(output / 'deployment.json')['active_runs'], {})
            self.assertEqual(set(read_json(output / 'baselines-integrity.json')), set(assignments))

    def test_live_status_reports_validation_failures_without_exposing_test_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(root / 'deployment.json', {'state': 'running', 'candidate': 'student', 'stage': 'report'})
            write_json(root / 'configs/student.json', {'training_milestones': [200, 400, 600, 800, 1000]})
            write_json(root / 'student/preflight.json', {'evaluation_notes': 100, 'test_notes': 200})
            for stage in ('baseline', 'test/baseline'):
                note = root / 'student' / stage / 'note-0000'
                write_json(note / 'subjects-result.json', {'subjects': [], 'errors': [{'error': 'malformed'}]})
                write_json(note / 'complete.json', {})
            (root / 'student/subject-training-updates.jsonl').write_text('{"cursor":8,"updates":1,"loss":1.5}\n')
            status = deploy.status(root)
            self.assertEqual(status['candidates']['student']['evaluations']['baseline']['subject_failures'], 1)
            self.assertEqual(status['candidates']['student']['tests']['baseline'], {'notes': 1, 'expected_notes': 200})
            self.assertEqual(status['candidates']['student']['training']['cursor'], 8)

    def test_missing_reserved_baseline_test_blocks_all_candidate_training(self):
        from sse_multivector import distillation_data
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            splits = root / "splits.json"
            write_json(splits, {"train": ["0", "1"], "validation": ["2", "3"], "test": ["4", "5"]})
            prepared = root / "subjects"
            distillation_data.prepare(root / "source.json", root / "annotations.json", root / "subjects.txt",
                None, "AS-test", None, 2, "test", prepared, tasks=("subjects",), splits_path=splits)
            config = root / "first.json"
            write_json(config, {"data": str(prepared), "model": "org/model", "revision": "a"*40,
                               "training_milestones": [1, 2], "evaluation_tasks": ["subjects"]})
            package = root / "package"
            deploy.prepare([config], package)
            calls = []
            def child(command, **kwargs):
                calls.append(command[-1])
                return type("Result", (), {"returncode": 0})()
            with patch.object(deploy, "run_process", side_effect=child), \
                    patch.object(deploy, "subject_stage_summary", return_value={"notes": 2}):
                with self.assertRaises(FileNotFoundError):
                    deploy.execute(package, root / "results")
            self.assertEqual(calls, ["baseline"])

    def test_completion_review_requires_verified_retrieval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(FileNotFoundError, 'retrieval-verification.json'):
                deploy.review_completion(root / 'package', root / 'operation')
            self.assertFalse((root / 'operation/launch/completion-review.json').exists())

    def test_cuda_fused_pilot_cannot_be_packaged_without_matched_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'candidate.json'
            write_json(path, {'device': 'cuda', 'fused_linear_cross_entropy': True, 'training_milestones': [1000]})
            with self.assertRaisesRegex(ValueError, 'requires matched GPU preparation'):
                deploy.prepare([path], root / 'inputs')

    def test_all_subject_baselines_are_verified_before_any_training(self):
        from sse_multivector import distillation_data, distillation_run
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            data_path = root / "subjects"
            distillation_data.prepare(root / "source.json", root / "annotations.json", root / "subjects.txt",
                None, "AS-test", None, 2, "pilot", data_path, tasks=("subjects",))
            configs = []
            for name in ("first", "second"):
                path = root / (name + ".json")
                write_json(path, {"data": str(data_path), "model": "org/model", "revision": "a"*40,
                                  "training_milestones": [2, 4], "evaluation_tasks": ["subjects"]})
                configs.append(path)
            package, output = root / "package", root / "results"
            changed = read_json(configs[1])
            write_json(configs[1], {**changed, "training_milestones": [1, 4]})
            with self.assertRaisesRegex(ValueError, "shared pilot inputs or recipe differ"):
                deploy.prepare(configs, root / "mixed-inputs")
            write_json(configs[1], changed)
            deploy.prepare(configs, package)
            calls = []
            def child(command, timeout, **kwargs):
                name = Path(command[3]).stem
                mode = command[-1]
                calls.append((name, mode))
                return type("Result", (), {"returncode": 0})()
            with patch.object(deploy, "run_process", side_effect=child), \
                    patch.object(deploy, "subject_stage_summary", return_value={"notes": 2}), \
                    patch.object(deploy, "verify_subject_run", return_value={"status": "complete"}):
                deploy.execute(package, output)
            self.assertEqual(calls, [("first", "baseline"), ("second", "baseline"),
                                     ("first", "report"), ("second", "report")])
            calls.clear()
            with patch.object(deploy, "run_process", side_effect=child), \
                    patch.object(deploy, "subject_stage_summary", side_effect=ValueError("missing response")):
                with self.assertRaisesRegex(ValueError, "missing response"):
                    deploy.execute(package, root / "broken")
            self.assertEqual(calls, [("first", "baseline")])

    def test_paired_preparation_requires_identical_pilot_recipe(self):
        from sse_multivector import distillation_data
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            data = root / "subjects"
            manifest = distillation_data.prepare(root / "source.json", root / "annotations.json", root / "subjects.txt",
                None, "AS-test", None, 2, "pilot", data, tasks=("subjects",))
            pilot = root / "pilot/candidate.json"
            prep = root / "prep/candidate.json"
            config = {"data": str(data), "model": "org/model", "revision": "a"*40,
                      "training_milestones": [2, 4], "evaluation_tasks": ["subjects"], "learning_rate": .0001,
                      "max_new_tokens": {"subjects": 8}}
            write_json(pilot, config)
            prepared = {**config, "training_milestones": [1, 2], "preparation": {
                "train_note_ids": manifest["train_note_ids"][:2], "evaluation_note_ids": manifest["evaluation_note_ids"][:1],
                "max_new_tokens": 4, "cache_fill_tokens": 16}}
            write_json(prep, prepared)
            package = root / "package"
            deploy.prepare([pilot], package, preparation_configs=[prep])
            job = deploy.verify_package(package)
            self.assertEqual(job["preparation_runs"], ["preparation-configs/candidate.json"])
            self.assertEqual(job["timeout_seconds"], None)
            write_json(prep, {**prepared, "learning_rate": .01})
            with self.assertRaisesRegex(ValueError, "preparation recipe differs"):
                deploy.prepare([pilot], root / "bad", preparation_configs=[prep])

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
    @unittest.skipUnless(os.environ.get('DISTILLATION_VOLUME_STAGE') == 'seed', 'requires the volume replacement rehearsal')
    def test_seed_volume_before_container_replacement(self):
        root = self.fixture_package('volume-replacement', {'training_milestones': [1, 2, 3, 4],
            'batch_size': 1, 'gradient_accumulation_steps': 8, 'evaluation_tasks': ['subjects'],
            'subject_batching': {'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4}}, seconds=None, test_notes=True)
        self.run_package(root / 'inputs', root / 'original', local_volume=True)

    @unittest.skipUnless(os.environ.get('DISTILLATION_VOLUME_STAGE') == 'recover', 'requires the volume replacement rehearsal')
    def test_recover_volume_after_container_replacement(self):
        from sse_multivector.distillation_run import file_hashes
        root = Path(os.environ['DISTILLATION_DEPLOY_OUTPUT']) / 'volume-replacement'
        old = root / 'original'
        write_json(old / 'launch/destruction-confirmation.json', {'instance_id': 'offline-fixture',
            'absent_from_complete_inventory': True, 'absence_observations': 2})
        before = file_hashes(old / 'result/work/results')
        result = self.run_package(root / 'inputs', root / 'replacement', local_volume=True, recover_from=old)
        after = file_hashes(result)
        for path, digest in before.items():
            if path.endswith('.log'):
                self.assertTrue((result / path).read_bytes().startswith((old / 'result/work/results' / path).read_bytes()))
            elif path != 'deployment.json':
                self.assertEqual(after[path], digest, path)
        receipt = read_json(root / 'replacement/launch/volume-prepared.json')['remote_receipt']
        self.assertTrue(receipt['recovered'])
        write_json(root / 'replacement-checks.json', {'unchanged_files': before,
            'receipt': receipt, 'checkpoint_and_answers_reused': True})

    def test_two_gpu_prep_continues_into_fresh_pilot_and_verifies_retrieved_results(self):
        from sse_multivector.distillation_run import load_data
        root = self.fixture_package('prep-then-pilot', {
            'training_milestones': [1, 2, 3, 4], 'batch_size': 1, 'gradient_accumulation_steps': 8,
            'evaluation_tasks': ['subjects'], 'subject_batching': {'budget_bytes': 8*1024*1024,
                'workspace_bytes': 0, 'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4}},
            seconds=None, test_notes=True)
        paths, preparations = [], []
        for name in ('first', 'second'):
            path = root / (name + '.json')
            paths.append(path)
            config = read_json(path)
            data = load_data(config['data'])
            prep = root / 'prep-configs' / (name + '.json')
            write_json(prep, {**config, 'training_milestones': [2, 4], 'preparation': {
                'max_new_tokens': 4, 'cache_fill_tokens': 16,
                'train_note_ids': data['manifest']['train_note_ids'],
                'evaluation_note_ids': data['manifest']['evaluation_note_ids']}})
            preparations.append(prep)
        package = root / 'combined-inputs'
        deploy.prepare(paths, package, preparation_configs=preparations,
                       gpu_assignments={'first': 0, 'second': 1})
        result = self.run_package(package, root / 'operation', copy_while_running=True)
        checked = deploy.verify_results(package, result)
        self.assertEqual(checked['status'], 'complete')
        self.assertEqual(set(checked['candidates']), {'first', 'second'})
        self.assertEqual(read_json(result / 'deployment.json')['gpu_assignments'], {'first': 0, 'second': 1})
        self.assertEqual(read_json(result / 'deployment.json')['active_runs'], {})
        reviewed = deploy.review_completion(package, root / 'operation')
        self.assertTrue(reviewed['complete'])
        self.assertEqual(reviewed['instance_id'], 'offline-fixture')
        for name in checked['candidates']:
            self.assertEqual(read_json(result / 'preparation' / name / 'report.json')['training']['updates'], 2)
            self.assertEqual(read_json(result / name / 'checkpoints/checkpoint-1/training.json')['updates'], 1)
            self.assertEqual(read_json(result / name / 'report.json')['training']['updates'], 4)
            self.assertFalse((result / 'preparation' / name / 'test').exists())
            self.assertEqual(set(checked['candidates'][name]['test']), {'review_status', 'baseline', 'checkpoint-4'})
            for stage in ('baseline', 'checkpoint-4'):
                self.assertEqual(checked['candidates'][name]['test'][stage]['notes'], 2)
                answers = read_json(result / name / 'test' / stage / 'results.json')
                self.assertEqual([row['note_id'] for row in answers], ['6', '7'])
        missing = result / 'first/test/checkpoint-4/note-0001/subjects.json'
        saved = missing.read_bytes()
        missing.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            deploy.verify_results(package, result)
        with self.assertRaisesRegex(Exception, 'file set does not match the sealed manifest'):
            deploy.review_completion(package, root / 'operation')
        missing.write_bytes(saved)
        report = read_json(result / 'first/report.json')
        report['checkpoints'].pop()
        write_json(result / 'first/report.json', report)
        with self.assertRaisesRegex(ValueError, 'comparison report differs'):
            deploy.verify_results(package, result)
        with self.assertRaisesRegex(Exception, 'integrity verification'):
            deploy.review_completion(package, root / 'operation')

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
        # Interrupt a real SSH transfer after 100 bytes. The production
        # receiver must retain those bytes without publishing the checkpoint.
        import json
        import shlex
        import subprocess
        record = {'path': 'work/results/checkpoints/adapter/weights.bin',
                  'bytes': (checkpoint / 'weights.bin').stat().st_size,
                  'sha256': sha256(checkpoint / 'weights.bin')}
        request = operation / 'interrupted-copy.json'
        write_json(request, [record])
        producer = subprocess.Popen(module.remote_arguments(context, key, endpoint, '_remote-copy',
            '--files', shlex.quote(json.dumps([record]))), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            prefix = producer.stdout.read(100)
            self.assertEqual(len(prefix), 100)
        finally:
            producer.stdout.close()
            producer.terminate()
            producer.wait(timeout=20)
        interrupted = subprocess.run([sys.executable, '-B', str(context.operator_path),
            '--root', str(operation), '--config', str(config), '_receive-copy', '--request', str(request)],
            input=prefix, capture_output=True, timeout=20)
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertIn(b'ended early', interrupted.stderr)
        self.assertFalse(weights.exists())
        self.assertEqual((operation / 'progressive/partial' / record['path']).read_bytes(), prefix)
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
        self.assertEqual(groups[0][0]['offset'], 100)
        self.assertEqual(sha256(weights), sha256(checkpoint / 'weights.bin'))
        self.assertEqual(sha256(subject), sha256(note / 'subjects.json'))
        write_json(root / 'transfer-checks.json', {'groups': groups, 'response_before_checkpoint': True,
                                                'checkpoint_sha256': sha256(weights), 'subject_sha256': sha256(subject)})

    def run_package(self, inputs, root, expected=0, stop=False, copy_while_running=False,
                    continue_after_checkpoint=False, local_volume=False, recover_from=None):
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
        job = deploy.verify_package(inputs)
        gpu_count = max(job.get('gpu_assignments', {}).values(), default=0) + 1
        settings['offer_equals']['num_gpus'] = offer['num_gpus'] = gpu_count
        if local_volume:
            settings['local_volume'] = {'id': 881, 'machine_id': offer['machine_id']}
        if recover_from is not None:
            settings['recover_from'] = str(recover_from)
            settings['label'] += '-replacement'
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
        write_json(root / 'launch/create-result.json', {'success': True, 'new_contract': 'offline-fixture'})
        shutil.copyfile(ledger, root / 'launch/reserved-budget-ledger.json')
        write_json(root / 'launch/full-build-reservation.json', {'ledger_sha256': sha256(ledger)})
        shutil.copyfile(config, root / 'launch/operation-contract.json')
        remote = '/workspace/oracle-full-build'
        module.verify_local_ssh(context)
        if local_volume:
            module.ensure_remote_volume(context, key, endpoint, root / 'launch', 'offline-fixture')
        module.tar_upload_directory(context, key, endpoint, root / 'transport', remote + '/transport')
        module.tar_upload_directory(context, key, endpoint, root / 'launch', remote + '/launch')
        # Each independent test uses a fresh operation on the same SSH target.
        if not local_volume:
            module.completed_process([*module.ssh_arguments(context, key, endpoint),
                'rm -rf /workspace/oracle-full-build/work /workspace/oracle-full-build/package /workspace/oracle-full-build/preparation-attempts'])
        def call(operation, *args):
            return module.remote_json(context, key, endpoint, operation, *args)
        self.assertTrue(call('_remote-verify-transfer')['verified'])
        deadline = time.monotonic() + 240
        while not call('_remote-prepare').get('prepared'):
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.2)
        if recover_from is not None:
            with patch.object(module, 'record_pre_worker_cost'):
                attempt_id = module.ensure_worker_started(context, 'offline-fixture', key, endpoint)
            self.assertEqual(attempt_id, '002')
        else:
            attempt_id = '001'
            started = call('_remote-worker', '--attempt', attempt_id)
            module.atomic_json(root / f'launch/worker-invocations/{attempt_id}.json',
                               {'attempt_id': attempt_id, 'instance_id': 'offline-fixture'})
            module.publish_worker_acknowledgement(context, 'offline-fixture', attempt_id, started)
        copier = module.start_progressive_copy(context, key, endpoint) if copy_while_running else None
        if copier is not None:
            self.addCleanup(lambda: copier.terminate() if copier.poll() is None else None)
        copied_before_terminal = None
        interruption_requested = False
        if stop:
            time.sleep(2)
            call('_remote-stop', '--attempt', attempt_id)
        while True:
            state = call('_remote-status', '--attempt', attempt_id)
            if continue_after_checkpoint and not interruption_requested:
                checkpoints = state.get('progress', {}).get('candidates', {}).get('first', {}).get('checkpoints', [])
                if checkpoints:
                    call('_remote-stop', '--attempt', '001', '--incomplete-stop-approval',
                         'Interrupt the offline SSH rehearsal after its first saved checkpoint')
                    interruption_requested = True
            if copier is not None and state['state'] == 'running':
                local = root / 'result.next/work/results'
                names = [Path(path).stem for path in job['runs']] if job.get('gpu_assignments') else ['first']
                # The paired toy run can finish its main updates faster than
                # a complete SSH copy. Its prep checkpoints are already frozen
                # while baselines run; verify early copies from both workers.
                checkpoint_root = local / 'preparation' if job.get('preparation_runs') else local
                note_groups = [list((local / name).glob('baseline/note-*/complete.json')) for name in names]
                checkpoint_groups = [list((checkpoint_root / name).glob('checkpoints/checkpoint-*/complete.json'))
                                     for name in names]
                notes = [path for group in note_groups for path in group]
                checkpoints = [path for group in checkpoint_groups for path in group]
                if all(note_groups) and all(checkpoint_groups) and copied_before_terminal is None:
                    from sse_multivector.distillation_run import verify_saved
                    self.assertTrue(all(verify_saved(p.parent) for p in notes + checkpoints))
                    copied_before_terminal = {str(p.relative_to(root / 'result.next')): p.stat().st_mtime_ns for p in notes + checkpoints}
                    write_json(root / 'copied-while-running.json', {'remote_state': state, 'files': copied_before_terminal})
            if state['state'] == 'terminal':
                break
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.1 if continue_after_checkpoint else .5)
        (root / 'result.next').mkdir(exist_ok=True)
        module.ensure_retrieved(context, 'offline-fixture', key, endpoint, attempt_id)
        if continue_after_checkpoint:
            self.assertTrue(interruption_requested, state)
            self.assertNotEqual(state['exit_status'], 0)
            inventory = call('_remote-progress')['files']
            preserved = {r['path']: r['sha256'] for r in inventory}
            self.assertTrue(any('/baseline/' in p for p in preserved))
            self.assertTrue(any('/checkpoints/checkpoint-' in p for p in preserved))
            receipt_hash = sha256(root / 'launch/retrieval-verification.json')
            with patch.object(module, 'ensure_ssh', return_value=(key, endpoint)):
                resumed = module.resume(context, 'Continue the frozen offline subject pilot from saved work')
                # Repeated delivery reconciles the same continuation.
                duplicate = module.resume(context, 'Continue the frozen offline subject pilot from saved work')
            self.assertEqual(resumed['attempt_id'], '002')
            self.assertEqual(duplicate['attempt_id'], '002')
            while True:
                state = call('_remote-status', '--attempt', '002')
                if state['state'] == 'terminal':
                    break
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.2)
            module.ensure_retrieved(context, 'offline-fixture', key, endpoint, '002')
            self.assertEqual(sha256(root / 'retrieval-attempts/001/retrieval-verification.json'), receipt_hash)
            self.assertEqual(read_json(root / 'launch/retrieval-verification.json')['attempt_id'], '002')
            for name, digest in preserved.items():
                self.assertEqual(sha256(root / 'result.next' / name), digest, name)
            self.assertFalse((root / 'launch/completion-review.json').exists())
            self.assertTrue(module.publish_verified_result(context, '002'),
                            (root / 'result.next/work/full-build-attempts/002/full-build.log').read_text()
                            if (root / 'result.next').exists() else '')
            write_json(root / 'continuation-checks.json', {'attempts': ['001', '002'],
                'preserved_files': preserved, 'first_retrieval_sha256': receipt_hash,
                'final_retrieval_sha256': sha256(root / 'launch/retrieval-verification.json')})
            return root / 'result/work/results'
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
            self.assertEqual(state['exit_status'], 0, (root / f'result.next/work/full-build-attempts/{attempt_id}/full-build.log').read_text())
            self.assertTrue(module.publish_verified_result(context, attempt_id))
            results = root / 'result/work/results'
            self.assertEqual(read_json(results / 'deployment.json')['state'], 'complete')
            # A new SSH call cannot start a second execution after completion.
            self.assertEqual(call('_remote-worker', '--attempt', attempt_id)['exit_status'], 0)
        else:
            self.assertNotEqual(state['exit_status'], 0)
            results = root / 'result.next/work/results'
        return results

    def fixture_package(self, name, changes=None, seconds=180, through='report', test_notes=False,
                        gpu_assignments=None):
        root = Path(os.environ['DISTILLATION_DEPLOY_OUTPUT']) / name
        root.mkdir(parents=True)
        config = read_json(Path(os.environ['DISTILLATION_TEST_OUTPUT']) / 'config.json')
        config.update(changes or {})
        if 'training_milestones' in config:
            from sse_multivector import distillation_data
            source = Path(os.environ['DISTILLATION_TEST_OUTPUT'])
            splits = None
            if test_notes:
                splits = root / 'splits.json'
                write_json(splits, {'train': ['0', '1', '2', '3'],
                                    'validation': ['4', '5'], 'test': ['6', '7']})
            distillation_data.prepare(source / 'source.json', source / 'annotations.json', source / 'subjects.txt',
                None, 'AS-test', None, 2, 'test', root / 'subject-data', tasks=('subjects',), splits_path=splits)
            config['data'] = str(root / 'subject-data')
            for key in ('mask_prompt', 'mask_batch_size', 'subject_fraction', 'max_steps', 'save_steps'):
                config.pop(key)
            config['max_new_tokens'] = {'subjects': config['max_new_tokens']['subjects']}
        paths = []
        for candidate in ('first', 'second'):
            path = root / (candidate + '.json')
            write_json(path, config)
            paths.append(path)
        deploy.prepare(paths, root / 'inputs', seconds, through=through, gpu_assignments=gpu_assignments)
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

    def test_subject_pilot_continues_saved_checkpoint_and_refreshes_retrieval_over_ssh(self):
        policy = {'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                  'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4}
        root = self.fixture_package('continued-subject-pilot', {'training_milestones': [1, 2, 3, 4],
            'batch_size': 1, 'gradient_accumulation_steps': 8,
            'evaluation_tasks': ['subjects'], 'subject_batching': policy}, seconds=None, test_notes=True,
            gpu_assignments={'first': 0, 'second': 1})
        result = self.run_package(root / 'inputs', root / 'operation', continue_after_checkpoint=True)
        from sse_multivector.distillation_run import verify_saved
        for name in ('first', 'second'):
            self.assertEqual(read_json(result / name / 'report.json')['training'], {'examples': 4, 'updates': 4})
            for stage in ('baseline', 'checkpoints/checkpoint-1', 'checkpoints/checkpoint-4',
                          'evaluations/checkpoint-4', 'test/baseline', 'test/checkpoint-4'):
                self.assertTrue(verify_saved(result / name / stage))

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
