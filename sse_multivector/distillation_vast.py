"""Describe distillation for vast/package.py. No provider calls or paid actions."""
import argparse
from pathlib import Path
import re

from sse_multivector.distillation_deploy import check_offer, verify_package, REMOTE_PYTHON
from sse_multivector.distillation_run import read_json, write_json


def make_spec(settings, offer, package, image):
    check_offer(settings, offer)
    job = verify_package(package)
    if not re.fullmatch(re.escape(settings['image_repository']) + r'@sha256:[a-f0-9]{64}', image):
        raise ValueError('supply the published image registry digest')
    if (job['timeout_seconds'] is None and settings['worker_timeout_seconds'] is not None or
            job['timeout_seconds'] is not None and settings['worker_timeout_seconds'] is not None
            and job['timeout_seconds'] > settings['worker_timeout_seconds']):
        raise ValueError('package exceeds the approved worker timeout')
    return {'version': 2, 'label': settings['label'], 'offer': offer, 'image': image,
        'disk_gb': settings['disk_gb'], 'onstart': settings['onstart'], 'ssh_direct': settings['ssh_direct'],
        'python': REMOTE_PYTHON,
        'inputs': [{'source': str(Path(package).resolve()), 'destination': 'inputs'}],
        'command': [REMOTE_PYTHON, '-m', 'sse_multivector.distillation_deploy', 'execute',
                    '--package', '../package/inputs', '--output', 'results'],
        'environment': {'PYTHONPATH': '/work',
            'PATH': '/opt/distillation-venv/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'LD_LIBRARY_PATH': '/usr/local/nvidia/lib:/usr/local/nvidia/lib64',
            'HF_HUB_DISABLE_TELEMETRY': '1', 'TOKENIZERS_PARALLELISM': 'false',
            'PYTHONUNBUFFERED': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
        'outputs': ['results'],
        'resumable': all('training_milestones' in read_json(Path(package) / path) for path in job['runs']),
        'status_command': [REMOTE_PYTHON, '-m', 'sse_multivector.distillation_deploy', 'status', '--output', 'results'],
        'progressive_copy': settings.get('progressive_copy', {
            'poll_seconds': 5, 'bytes_per_second': 8 * 1024 * 1024, 'timeout_seconds': 900}),
        'limits': {'maximum_charge_cents': int(settings['approved_maximum_usd'] * 100),
            'maximum_hourly_usd': settings['offer_maximums']['dph_total'],
            'session_seconds': settings['rental_hours'] * 3600, 'cleanup_seconds': 900,
            'work_seconds': job['timeout_seconds'],
            'setup_cost_cents': settings.get('setup_cost_cents', 500),
            'manual_stop_cost_cents': settings.get('manual_stop_cost_cents', 2460),
            'inbound_gb': settings['inbound_gb'], 'outbound_gb': settings['outbound_gb']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, default=Path('sse_multivector/distillation/vast-launch.json'))
    parser.add_argument('--offer', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    write_json(args.output, make_spec(read_json(args.settings), read_json(args.offer), args.package, args.image))


if __name__ == '__main__':
    main()
