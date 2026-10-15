"""Download frozen public model files and verify the persistent cache offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import time

from gte.full_build_package import verify_manifest, write_manifest
from sse_multivector.distillation_run import read_json, sha256, write_json


def validate(manifest):
    if (manifest.get('version') != 1 or type(manifest.get('reserve_bytes')) is not int
            or manifest['reserve_bytes'] < 0 or not manifest.get('models')):
        raise ValueError('invalid model cache manifest')
    seen = set()
    for model in manifest['models']:
        key = (model['model'], model['revision'])
        if (key in seen or not re.fullmatch(r'[\w.-]+/[\w.-]+', key[0])
                or not re.fullmatch(r'[a-f0-9]{40}', key[1]) or not model.get('files')):
            raise ValueError('cache requires distinct models at immutable revisions')
        seen.add(key)
        names = set()
        for record in model['files']:
            name = record['path']
            path = PurePosixPath(name)
            digest = set(record) & {'sha256', 'git_blob_sha1'}
            if (not name or path.is_absolute() or '..' in path.parts or str(path) != name
                    or '\\' in name or name in names or len(digest) != 1
                    or type(record.get('size')) is not int or record['size'] < 0):
                raise ValueError('invalid required cache file')
            algorithm, = digest
            if not re.fullmatch(r'[a-f0-9]{%d}' % (64 if algorithm == 'sha256' else 40), record[algorithm]):
                raise ValueError('invalid cache checksum')
            names.add(name)
    return manifest


def bind(manifest, configs):
    validate(manifest)
    expected = {(c['model'], c.get('revision')) for c in configs}
    if expected != {(m['model'], m['revision']) for m in manifest['models']}:
        raise ValueError('cache models or revisions differ from the frozen runs')


def hub_file(model, record, *, offline, force=False):
    from huggingface_hub import hf_hub_download
    home = Path(os.environ['HF_HOME']).resolve()
    path = Path(hf_hub_download(model['model'], record['path'], revision=model['revision'],
        cache_dir=home / 'hub', local_files_only=offline, force_download=force, token=False,
        endpoint=os.environ.get('HF_ENDPOINT', 'https://huggingface.co')))
    if not path.resolve().is_relative_to(home):
        raise ValueError('model file escapes the persistent cache')
    return path


def check_file(path, record):
    if path.stat().st_size != record['size']:
        raise ValueError('size mismatch')
    if 'sha256' in record:
        checksum = sha256(path)
        expected = record['sha256']
    else:
        digest = hashlib.sha1(('blob %d\0' % record['size']).encode())
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(8*1024*1024), b''):
                digest.update(block)
        checksum, expected = digest.hexdigest(), record['git_blob_sha1']
    if checksum != expected:
        raise ValueError('checksum mismatch')
    return checksum


def verify(manifest_path, output=None):
    manifest = validate(read_json(manifest_path))
    started = time.time()
    report = {'state': 'running', 'offline': True, 'manifest_sha256': sha256(manifest_path),
              'started': started, 'files': []}
    for model in manifest['models']:
        for record in model['files']:
            result = {'model': model['model'], 'revision': model['revision'], **record}
            try:
                result['verified_checksum'] = check_file(hub_file(model, record, offline=True), record)
                result['verified'] = True
            except Exception as error:
                result.update(verified=False, error_type=type(error).__name__)
            report['files'].append(result)
    report.update(state='complete' if all(r['verified'] for r in report['files']) else 'failed',
                  finished=time.time())
    if output is not None:
        write_json(output, report)
    if report['state'] != 'complete':
        raise ValueError('cache verification failed; missing or corrupt required files')
    return report


def prepare(config_paths, output, reserve_bytes=0):
    """Freeze required file hashes from public Hub metadata; fetch only the small index."""
    from huggingface_hub import HfApi, hf_hub_download
    from sse_multivector.distillation_deploy import code_hashes
    models = sorted({(c['model'], c['revision']) for c in map(read_json, config_paths)})
    manifest = {'version': 1, 'reserve_bytes': reserve_bytes, 'models': []}
    api = HfApi(token=False, endpoint=os.environ.get('HF_ENDPOINT'))
    for name, revision in models:
        if not re.fullmatch(r'[a-f0-9]{40}', revision):
            raise ValueError('remote models require an immutable revision')
        info = api.model_info(name, revision=revision, files_metadata=True)
        if info.sha != revision:
            raise ValueError('Hub returned a different model revision')
        files = {f.rfilename: f for f in info.siblings}
        selected = {n for n in files if n in ('config.json', 'generation_config.json',
            'special_tokens_map.json', 'added_tokens.json', 'vocab.json', 'merges.txt',
            'chat_template.jinja', 'tokenizer.model', 'spiece.model') or n.startswith('tokenizer')
            or n.startswith('chat_templates/')}
        if not {'config.json', 'tokenizer_config.json'} <= selected:
            raise ValueError('model configuration or tokenizer configuration missing')
        if 'model.safetensors.index.json' in files:
            index = read_json(hf_hub_download(name, 'model.safetensors.index.json',
                revision=revision, token=False, endpoint=os.environ.get('HF_ENDPOINT')))
            shards = set(index['weight_map'].values())
            if not shards or any(n not in files or not n.endswith('.safetensors') for n in shards):
                raise ValueError('weights index references missing shards')
            selected.update(shards | {'model.safetensors.index.json'})
        elif 'model.safetensors' in files:
            selected.add('model.safetensors')
        else:
            raise ValueError('safetensors weights missing')
        records = []
        for filename in sorted(selected):
            entry = files[filename]
            lfs = entry.lfs
            records.append({'path': filename, 'size': entry.size,
                **({'sha256': lfs.sha256} if lfs else {'git_blob_sha1': entry.blob_id})})
        manifest['models'].append({'model': name, 'revision': revision, 'files': records})
    validate(manifest)
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    staging = output.with_name(output.name + '.partial')
    staging.mkdir(parents=True)
    try:
        write_json(staging / 'model-cache.json', manifest)
        write_json(staging / 'job.json', {'cache_manifest': 'model-cache.json',
            'timeout_seconds': None, 'code': code_hashes()})
        write_manifest(staging, staging / 'manifest.json', 'distillation-model-cache')
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return sha256(output / 'manifest.json')


def verify_package(package):
    from sse_multivector.distillation_deploy import code_hashes
    package = Path(package)
    verify_manifest(package, package / 'manifest.json')
    job = read_json(package / 'job.json')
    if job['code'] != code_hashes() or job['cache_manifest'] != 'model-cache.json':
        raise ValueError('cache package differs from the runtime')
    validate(read_json(package / job['cache_manifest']))
    return job


def download(manifest_path, output):
    """Retain good files, resume missing downloads and repair corrupted blobs."""
    manifest = validate(read_json(manifest_path))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    home = Path(os.environ['HF_HOME']).resolve()
    identity = home.parent / 'volume-identity.json'
    if not identity.is_file():
        raise ValueError('download workload requires the verified persistent volume')
    home.mkdir(parents=True, exist_ok=True)
    probe = home / '.download-write-probe'
    probe.write_bytes(b'persistent cache write/read check')
    readable = probe.read_bytes() == b'persistent cache write/read check'
    probe.unlink()
    if not readable:
        raise ValueError('persistent cache write/read check failed')
    write_json(output / 'volume.json', {'cache_path': str(home), 'write_read_verified': readable,
        'volume_root': str(home.parent),
        'volume_identity': read_json(identity) if identity.exists() else None,
        'disk_free_bytes': shutil.disk_usage(home).free, 'observed': time.time()})
    report = {'state': 'running', 'manifest_sha256': sha256(manifest_path),
              'started': time.time(), 'files': []}
    def event(**values):
        with (output / 'download.jsonl').open('a') as log:
            log.write(json.dumps({'time': time.time(), **values})+'\n')
        write_json(output / 'verification.json', report)
    try:
        missing = []
        for model in manifest['models']:
            for record in model['files']:
                try:
                    check_file(hub_file(model, record, offline=True), record)
                except Exception:
                    missing.append(record['size'])
        required = sum(missing) + max(missing, default=0) + manifest['reserve_bytes']
        if shutil.disk_usage(home).free < required:
            raise ValueError('insufficient persistent storage for downloads and saved work')
        for model in manifest['models']:
            for record in model['files']:
                report['active_file'] = {'model': model['model'], 'revision': model['revision'],
                                         'path': record['path']}
                started, force = time.time(), False
                try:
                    path = hub_file(model, record, offline=True)
                except Exception:
                    path = None
                if path is not None:
                    try:
                        checksum = check_file(path, record)
                    except ValueError:
                        force = True
                reused = path is not None and not force
                if path is None or force:
                    event(stage='download', model=model['model'], path=record['path'], bytes=record['size'])
                    path = hub_file(model, record, offline=False, force=force)
                    checksum = check_file(path, record)
                result = {'model': model['model'], 'revision': model['revision'], **record,
                    'verified': True, 'verified_checksum': checksum, 'reused': reused,
                    'seconds': time.time()-started}
                report['files'].append(result)
                event(stage='verified', **result)
        report['state'] = 'complete'
        report.pop('active_file', None)
    except Exception as error:
        report.update(state='failed', error_type=type(error).__name__)
        event(stage='failed', error_type=type(error).__name__)
        raise ValueError('model download failed; see saved verification and download log') from None
    finally:
        report['finished'] = time.time()
        write_json(output / 'verification.json', report)
    return report


def verify_results(manifest_path, output, expected_volume=None):
    """Account for every required file in the retrieved download evidence."""
    manifest, output = validate(read_json(manifest_path)), Path(output)
    report = read_json(output / 'verification.json')
    expected = {(m['model'], m['revision'], f['path']): f
                for m in manifest['models'] for f in m['files']}
    files = report.get('files', [])
    actual = {(f['model'], f['revision'], f['path']): f for f in files}
    if (report.get('state') != 'complete' or report.get('manifest_sha256') != sha256(manifest_path)
            or set(actual) != set(expected) or len(files) != len(expected)):
        raise ValueError('required cache files missing from the completion report')
    for key, record in expected.items():
        saved = actual[key]
        checksum = record.get('sha256', record.get('git_blob_sha1'))
        if (any(saved.get(k) != v for k, v in record.items()) or saved.get('verified') is not True
                or saved.get('verified_checksum') != checksum):
            raise ValueError('required cache file checksum evidence differs')
    volume = read_json(output / 'volume.json')
    if (volume.get('write_read_verified') is not True or expected_volume is not None
            and volume.get('volume_identity') != expected_volume):
        raise ValueError('download volume verification differs')
    events = [json.loads(line) for line in (output / 'download.jsonl').read_text().splitlines()]
    verified = {(r['model'], r['revision'], r['path']) for r in events if r.get('stage') == 'verified'}
    if not set(expected) <= verified:
        raise ValueError('required cache files missing from the download log')
    return {'complete': True, 'manifest_sha256': sha256(manifest_path),
            'files': len(expected), 'bytes': sum(f['size'] for f in expected.values()),
            'volume': volume, 'download_seconds': report['finished']-report['started']}


def review_completion(package, operation):
    from vast import runner
    package, operation = Path(package), Path(operation).resolve()
    job = verify_package(package)
    context = runner.Context.load(argparse.Namespace(root=operation,
        config=operation / 'operation-contract.json', operation='status'))
    receipt_path = operation / 'launch/retrieval-verification.json'
    receipt = read_json(receipt_path)
    instance_id = runner.recorded_instance_id(context)
    if instance_id is None or receipt['instance_id'] != instance_id:
        raise ValueError('retrieval belongs to another instance')
    if sha256(package / 'manifest.json') != sha256(context.path('transport/workload/inputs/manifest.json')):
        raise ValueError('cache package differs from the frozen operation')
    candidate = context.path('result') if context.path('result').is_dir() else context.path('result.next')
    runner.verify_command_results(context, candidate)
    checked = verify_results(package / job['cache_manifest'], candidate / 'work/results',
                             context.config['local_volume'])
    write_json(operation / 'launch/completion-integrity.json', checked)
    review = {'complete': True, 'instance_id': instance_id,
        'operation_contract_sha256': sha256(context.config_path),
        'retrieval_verification_sha256': sha256(receipt_path),
        'integrity_sha256': sha256(operation / 'launch/completion-integrity.json'),
        'checks': ['Every pinned weight, tokenizer and configuration file has matching checksum evidence.',
                   'Download log and selected physical volume write/read receipt are complete.',
                   'All required evidence was retrieved and independently verified locally.']}
    write_json(operation / 'launch/completion-review.json', review)
    runner.verify_completion_review(context, instance_id, None)
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    preparing = commands.add_parser('prepare')
    preparing.add_argument('--config', action='append', type=Path, required=True)
    preparing.add_argument('--output', type=Path, required=True)
    preparing.add_argument('--reserve-bytes', type=int, default=0)
    downloading = commands.add_parser('download')
    downloading.add_argument('--package', type=Path, required=True)
    downloading.add_argument('--output', type=Path, required=True)
    verifying = commands.add_parser('verify')
    verifying.add_argument('--manifest', type=Path, required=True)
    verifying.add_argument('--output', type=Path)
    reviewing = commands.add_parser('verify-results')
    reviewing.add_argument('--package', type=Path, required=True)
    reviewing.add_argument('--operation-root', type=Path, required=True)
    status = commands.add_parser('status')
    status.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.operation == 'prepare':
        result = {'package_sha256': prepare(args.config, args.output, args.reserve_bytes)}
    elif args.operation == 'download':
        job = verify_package(args.package)
        result = download(args.package / job['cache_manifest'], args.output)
    elif args.operation == 'verify':
        result = verify(args.manifest, args.output)
    elif args.operation == 'verify-results':
        result = review_completion(args.package, args.operation_root)
    else:
        receipt = args.output / 'verification.json'
        result = read_json(receipt) if receipt.exists() else {'state': 'starting'}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
