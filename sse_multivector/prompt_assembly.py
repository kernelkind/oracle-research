#!/usr/bin/env python3
"""Assemble pinned prompt parts before handing a complete file to the runner."""
import argparse
import hashlib
import json
import os
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


def compile_spec(spec_path):
    spec_path = spec_path.resolve()
    spec = json.loads(spec_path.read_bytes())
    fields = {'schema_version', 'prompt_id', 'output', 'parts'}
    if isinstance(spec, dict) and ('shared' in spec or 'companion' in spec):
        fields |= {'shared', 'companion'}
    if not isinstance(spec, dict) or set(spec) != fields:
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
    if 'shared' in spec:
        shared = pinned_file(spec['shared'], spec_path.parent)
        if sum(p == spec['shared'] for p in spec['parts']) != 1:
            raise ValueError('shared rules must occur exactly once in parts')
        if not shared.read_bytes() or content.count(shared.read_bytes()) != 1:
            raise ValueError('shared rules must occur exactly once in the prompt')
        if (not isinstance(spec['companion'], str) or not spec['companion']
                or not spec['companion'].endswith('.assembly.json')):
            raise ValueError('companion must name an assembly manifest')
    return spec, output, content


def paired_spec(spec_path, spec):
    companion_path = (spec_path.parent / spec['companion']).resolve()
    if companion_path == spec_path.resolve():
        raise ValueError('a prompt cannot be its own companion')
    other, output, content = compile_spec(companion_path)
    if ('shared' not in other
            or pinned_file(spec['shared'], spec_path.parent) != pinned_file(other['shared'], companion_path.parent)
            or spec['shared']['sha256'] != other['shared']['sha256']):
        raise ValueError('companion shared rules differ')
    return companion_path, other, output, content


def assemble(spec_path, command):
    spec_path = spec_path.resolve()
    spec, output, content = compile_spec(spec_path)
    if 'shared' in spec:
        _, _, other_output, other_content = paired_spec(spec_path, spec)
        if other_output.exists() and other_output.read_bytes() != other_content:
            raise ValueError('companion prompt differs from its assembly')
        if command == 'check' and not other_output.exists():
            raise ValueError('companion prompt is missing')
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


def synchronize(spec_path, rules_path, identifier, companion_identifier):
    """Publish a new pair from one rule change; never modify existing versions."""
    spec_path, rules_path = spec_path.resolve(), rules_path.resolve()
    spec, _, _ = compile_spec(spec_path)
    if 'shared' not in spec:
        raise ValueError('sync requires a paired assembly')
    companion_path, other, _, _ = paired_spec(spec_path, spec)
    assemble(spec_path, 'check')
    assemble(companion_path, 'check')
    rules = rules_path.read_bytes()
    rules.decode('utf-8')
    if not rules:
        raise ValueError('shared rules must not be empty')
    if rules_path == pinned_file(spec['shared'], spec_path.parent):
        raise ValueError('create a new shared-rules version before synchronizing')
    if identifier == companion_identifier:
        raise ValueError('paired prompts need distinct version IDs')
    publication = {}
    manifests = []
    for path, prior, new_id, peer_id in (
            (spec_path, spec, identifier, companion_identifier),
            (companion_path, other, companion_identifier, identifier)):
        old_name = re.fullmatch(r'(.+)-v([0-9]+)', prior['prompt_id'])
        new_name = re.fullmatch(r'(.+)-v([0-9]+)', new_id)
        if (not new_name or new_name[1] != old_name[1]
                or int(new_name[2]) <= int(old_name[2])):
            raise ValueError('sync requires a newer version of each prompt')
        directory = path.parent
        peer_directory = companion_path.parent if path == spec_path else spec_path.parent
        shared = dict(path=os.path.relpath(rules_path, directory), sha256=digest(rules))
        parts = [shared if part == prior['shared'] else part for part in prior['parts']]
        content = b''.join(part['text'].encode('utf-8') if 'text' in part
                          else (directory / part['path']).read_bytes() for part in parts)
        manifest = {**prior, 'prompt_id': new_id, 'parts': parts, 'shared': shared,
                    'output': dict(path=new_id + '.md', sha256=digest(content)),
                    'companion': os.path.relpath(peer_directory / (peer_id + '.assembly.json'), directory)}
        new_path = directory / (new_id + '.assembly.json')
        publication[new_path] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
        publication[directory / (new_id + '.md')] = content
        manifests.append(new_path)
    if len(publication) != 4:
        raise ValueError('paired publication paths overlap')
    for path in publication:
        if path.exists() or path.is_symlink():
            raise ValueError(f'publication already exists: {path}')
    created = []
    try:
        for path, content in publication.items():
            with path.open('xb') as stream:
                created.append(path)
                stream.write(content)
        for path in manifests:
            assemble(path, 'check')
    except Exception:
        for path in reversed(created):
            path.unlink()
        raise
    return manifests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'check', 'sync'))
    parser.add_argument('spec', type=Path)
    parser.add_argument('--rules', type=Path, help='sync: new versioned shared-rules file')
    parser.add_argument('--prompt-id', help='sync: next version of this prompt')
    parser.add_argument('--companion-id', help='sync: next version of its companion')
    args = parser.parse_args()
    options = (args.rules, args.prompt_id, args.companion_id)
    if args.command == 'sync' and not all(options):
        parser.error('sync requires --rules, --prompt-id and --companion-id')
    if args.command != 'sync' and any(value is not None for value in options):
        parser.error('sync options require the sync command')
    try:
        if args.command == 'sync':
            for path in synchronize(args.spec, args.rules, args.prompt_id, args.companion_id):
                print(f'sync: {path}')
            return
        output = assemble(args.spec, args.command)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{args.command}: {output}')


if __name__ == '__main__':
    main()
