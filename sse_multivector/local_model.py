#!/usr/bin/env python3
"""Single-attempt loopback model transport for the shared experiment workflow.

LOCAL_MODEL_URL selects an owned loopback server. No credentials, remote
provider fallback, response repair or automatic retries are supported.
"""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import os
import sys
import time
from urllib.parse import urlsplit

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = 'sse_multivector'


def identity():
    paths = [Path(__file__), Path(__file__).with_name('local_weight_model.py'),
             Path(__file__).with_name('distillation_run.py')]
    return {'runner_version': 'oracle-local-model-runner/1',
            'runner_sha256': hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()}


def endpoint(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', '::1'}
            or not parsed.port or parsed.username or parsed.password
            or parsed.path not in {'', '/'} or parsed.query or parsed.fragment):
        raise ValueError('LOCAL_MODEL_URL must be an explicit HTTP loopback host and port')
    return parsed


def call(request, url):
    import jsonschema
    required = {'provider', 'model', 'reasoning', 'prompt', 'timeout_seconds', 'transport'}
    if not required <= set(request) <= required | {'schema', 'max_output_tokens'}:
        raise ValueError('unexpected or missing local request fields')
    if request['provider'] != 'local' or request['transport'] != 'http':
        raise ValueError('local requests require provider local and transport http')
    if request['reasoning'] not in {'off', 'provider-default'}:
        raise ValueError('local transport supports off or provider-default reasoning')
    if not isinstance(request['prompt'], str) or not isinstance(request['model'], str):
        raise ValueError('model and prompt must be strings')
    if not 0 < request['timeout_seconds'] <= 3600:
        raise ValueError('local timeout must be within 3600 seconds')
    parsed = endpoint(url)
    body = {'model': request['model'], 'messages': [{'role': 'user', 'content': request['prompt']}],
            'reasoning': request['reasoning']}
    if 'max_output_tokens' in request:
        if type(request['max_output_tokens']) is not int or request['max_output_tokens'] < 1:
            raise ValueError('max_output_tokens must be positive')
        body['max_tokens'] = request['max_output_tokens']
    schema = request.get('schema')
    if schema is not None:
        jsonschema.Draft202012Validator.check_schema(schema)
        body['response_format'] = {'type': 'json_schema', 'json_schema': {'schema': schema}}
    result = {**identity(), 'provider': 'local', 'model': request['model'],
              'reasoning': request['reasoning'], 'transport': 'http',
              'prompt_sha256': hashlib.sha256(request['prompt'].encode()).hexdigest(),
              'schema_sha256': hashlib.sha256(json.dumps(schema, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() if schema is not None else None,
              'request': {'method': 'POST', 'url': url.rstrip('/') + '/complete', 'body': body},
              'http_attempts': 1, 'valid': False, 'error': None, 'usage': None,
              'raw_text': '', 'output': None, 'stop_reason': 'error', 'response_metadata': {}}
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=request['timeout_seconds'])
    start = time.monotonic()
    try:
        connection.request('POST', '/complete', json.dumps(body, ensure_ascii=False).encode(),
                           {'Content-Type': 'application/json'})
        response = connection.getresponse()
        reply = json.loads(response.read())
        result['response_metadata'] = {**reply.get('metadata', {}), 'http_status': response.status}
        if response.status != 200 or reply.get('model') != request['model']:
            raise ValueError(reply.get('error', 'local response model identity differs'))
        result.update(raw_text=reply['raw_text'], stop_reason=reply['stop_reason'], usage=reply['usage'])
        if reply['stop_reason'] != 'stop':
            raise ValueError('local model did not complete within its output limit')
        output = json.loads(reply['raw_text']) if schema is not None else reply['raw_text']
        if schema is not None:
            jsonschema.validate(output, schema)
        result.update(output=output, valid=True)
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    finally:
        connection.close()
        result['duration_seconds'] = time.monotonic() - start
    return result


def main():
    if sys.argv[1:] == ['--identity']:
        print(json.dumps(identity()))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    run.add_argument('--send', action='store_true', required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--config', type=Path, required=True)
    serve.add_argument('--port', type=int, required=True)
    name = commands.add_parser('model-name', help='print the exact configuration-bound checkpoint identity without loading weights')
    name.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'serve':
        from sse_multivector.local_weight_model import serve
        serve(args.config, args.port)
        return
    if args.command == 'model-name':
        from sse_multivector.local_weight_model import checkpoint_name
        print(checkpoint_name(json.loads(args.config.read_text()), hashlib.sha256(args.config.read_bytes()).hexdigest()))
        return
    result = call(json.load(sys.stdin), os.environ['LOCAL_MODEL_URL'])
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    if not result['valid']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
