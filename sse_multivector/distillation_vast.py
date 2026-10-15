"""Describe distillation for vast/package.py. No provider calls or paid actions."""
import argparse
from decimal import Decimal
from pathlib import Path
import re

from sse_multivector.distillation_deploy import check_offer, verify_package, REMOTE_PYTHON
from sse_multivector.distillation_run import read_json, write_json


def make_spec(settings, offer, package, image):
    job = verify_package(package)
    required_gpus = max(job.get('gpu_assignments', {}).values(), default=0) + 1
    if offer['num_gpus'] < required_gpus:
        raise ValueError(f'package requires {required_gpus} GPUs')
    return _make_spec(settings, offer, package, image, job,
        'sse_multivector.distillation_deploy', 'execute',
        all('training_milestones' in read_json(Path(package) / path) for path in job['runs']))


def make_cache_spec(settings, offer, package, image):
    from sse_multivector.distillation_cache import verify_package as verify_cache_package
    if 'local_volume' not in settings:
        raise ValueError('model download workload requires a local volume')
    return _make_spec(settings, offer, package, image, verify_cache_package(package),
                      'sse_multivector.distillation_cache', 'download', True)


def _make_spec(settings, offer, package, image, job, module, action, resumable):
    if settings.get('require_local_volume') and 'local_volume' not in settings:
        raise ValueError('this launch profile requires a local volume')
    check_offer(settings, offer)
    if not re.fullmatch(re.escape(settings['image_repository']) + r'@sha256:[a-f0-9]{64}', image):
        raise ValueError('supply the published image registry digest')
    if (job['timeout_seconds'] is None and settings['worker_timeout_seconds'] is not None or
            job['timeout_seconds'] is not None and settings['worker_timeout_seconds'] is not None
            and job['timeout_seconds'] > settings['worker_timeout_seconds']):
        raise ValueError('package exceeds the approved worker timeout')
    spec = {'version': 2, 'label': settings['label'], 'offer': offer, 'image': image,
        'disk_gb': settings['disk_gb'], 'onstart': settings['onstart'], 'ssh_direct': settings['ssh_direct'],
        'python': REMOTE_PYTHON,
        'inputs': [{'source': str(Path(package).resolve()), 'destination': 'inputs'}],
        'command': [REMOTE_PYTHON, '-m', module, action,
                    '--package', '../package/inputs', '--output', 'results'],
        'environment': {'PYTHONPATH': '/work',
            'PATH': '/opt/distillation-venv/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'LD_LIBRARY_PATH': '/usr/local/nvidia/lib:/usr/local/nvidia/lib64',
            'HF_HUB_DISABLE_TELEMETRY': '1', 'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1',
            'TOKENIZERS_PARALLELISM': 'false',
            'PYTHONUNBUFFERED': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
        'outputs': ['results'],
        'resumable': resumable,
        'status_command': [REMOTE_PYTHON, '-m', module, 'status', '--output', 'results'],
        'progressive_copy': settings.get('progressive_copy', {
            'poll_seconds': 5, 'bytes_per_second': 8 * 1024 * 1024, 'timeout_seconds': 900}),
        # The volume has its own ledger commitment, including time detached.
        # Keep that allowance out of the instance's reservation ceiling.
        'limits': {'maximum_charge_cents': int(100 * (
            Decimal(str(settings['approved_maximum_usd'])) -
            Decimal(str(settings.get('local_volume_maximum_usd', 0))))),
            'maximum_hourly_usd': settings['offer_maximums']['dph_total'],
            'session_seconds': settings['rental_hours'] * 3600, 'cleanup_seconds': 900,
            'work_seconds': job['timeout_seconds'],
            'setup_cost_cents': settings.get('setup_cost_cents', 500),
            'manual_stop_cost_cents': settings.get('manual_stop_cost_cents', 2460),
            'inbound_gb': settings['inbound_gb'], 'outbound_gb': settings['outbound_gb']}}
    if 'local_volume' in settings:
        volume = settings['local_volume']
        if (not isinstance(volume, dict) or set(volume) != {'id', 'machine_id'}
                or any(type(v) is not int or v <= 0 for v in volume.values())
                or volume['machine_id'] != offer['machine_id']):
            raise ValueError('local volume must identify the selected physical machine')
        spec['local_volume'] = dict(volume)
        spec['environment']['HF_HOME'] = '/workspace/oracle-full-build/model-cache'
        if 'recover_from' in settings:
            spec['recover_from'] = settings['recover_from']
            for key in ('reuse_work', 'recovery_reason'):
                if key in settings:
                    spec[key] = settings[key]
    elif 'recover_from' in settings:
        raise ValueError('replacement requires a local volume')
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, default=Path('sse_multivector/distillation/vast-launch.json'))
    parser.add_argument('--offer', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--download-only', action='store_true', help='one-GPU persistent model cache job')
    parser.add_argument('--local-volume-id', type=int, help='existing persistent Vast local volume')
    parser.add_argument('--local-volume-machine-id', type=int, help='physical machine owning that volume')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if (args.local_volume_id is None) != (args.local_volume_machine_id is None):
        parser.error('supply both --local-volume-id and --local-volume-machine-id')
    if args.output.exists():
        raise FileExistsError(args.output)
    settings = read_json(args.settings)
    if args.local_volume_id is not None:
        volume = {'id': args.local_volume_id, 'machine_id': args.local_volume_machine_id}
        if 'local_volume' in settings and settings['local_volume'] != volume:
            parser.error('CLI volume differs from the volume already bound in settings')
        settings['local_volume'] = volume
    builder = make_cache_spec if args.download_only else make_spec
    write_json(args.output, builder(settings, read_json(args.offer), args.package, args.image))


if __name__ == '__main__':
    main()
