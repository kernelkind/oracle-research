#!/usr/bin/env python3
"""Assemble pinned prompt parts before handing a complete file to the runner."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(content):
    return hashlib.sha256(content).hexdigest()


def pinned_file(record, directory):
    if not isinstance(record, dict) or set(record) != {'path', 'sha256'}:
        raise ValueError('a prompt file must have exactly path and sha256')
    if not isinstance(record['path'], str) or not record['path']:
        raise ValueError('a prompt file needs a nonempty path')
    if not isinstance(record['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', record['sha256']):
        raise ValueError('a prompt file needs a lowercase SHA-256')
    return (directory / record['path']).resolve()


def assemble(spec_path, command):
    spec_path = spec_path.resolve()
    spec = json.loads(spec_path.read_bytes())
    if not isinstance(spec, dict) or set(spec) != {'schema_version', 'prompt_id', 'output', 'parts'}:
        raise ValueError('assembly spec needs schema_version, prompt_id, output and parts')
    if type(spec['schema_version']) is not int or spec['schema_version'] != 1:
        raise ValueError('expected assembly schema_version 1')
    identifier = spec['prompt_id']
    if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*-v[0-9]+', identifier):
        raise ValueError('prompt_id must end in a version such as -v1')
    output = pinned_file(spec['output'], spec_path.parent)
    if output.name != identifier + '.md':
        raise ValueError('output filename must match prompt_id with a .md extension')
    if not isinstance(spec['parts'], list) or not spec['parts']:
        raise ValueError('assembly needs a nonempty list of parts')
    pieces = []
    for record in spec['parts']:
        if isinstance(record, dict) and set(record) == {'text'}:
            if not isinstance(record['text'], str):
                raise ValueError('literal prompt text must be a string')
            pieces.append(record['text'].encode('utf-8'))
            continue
        path = pinned_file(record, spec_path.parent)
        if path == output:
            raise ValueError('assembled prompt cannot be its own source')
        content = path.read_bytes()
        content.decode('utf-8')
        if digest(content) != record['sha256']:
            raise ValueError(f'prompt part SHA-256 differs: {path}')
        pieces.append(content)
    content = b''.join(pieces)
    if digest(content) != spec['output']['sha256']:
        raise ValueError('assembled prompt SHA-256 differs from the pinned output')
    if output.exists() or output.is_symlink():
        if output.read_bytes() != content:
            raise ValueError(f'existing prompt differs; create a new version: {output}')
    elif command == 'check':
        raise ValueError(f'assembled prompt is missing: {output}')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(content)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'check'))
    parser.add_argument('spec', type=Path)
    args = parser.parse_args()
    try:
        output = assemble(args.spec, args.command)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{args.command}: {output}')


if __name__ == '__main__':
    main()
