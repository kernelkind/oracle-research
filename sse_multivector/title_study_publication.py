"""Publish explicitly selected saved title studies without model or source writes."""
import json
from pathlib import Path
import re

from ._runner_bootstrap import shared
from .prepare_category_title_inputs import prepare
from .prompt_study_publication import _Sources, _json, _sha, _snapshot


FORMAT = 'title-study-publication-v1'
_SETTINGS = {'model', 'provider', 'reasoning_effort', 'max_output_tokens',
             'timeout_seconds', 'codex_version', 'wrapper_sha256',
             'response_schema_sha256'}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


class _Study:
    def __init__(self, source, metadata, selection):
        self.source, self.metadata, self.selection = source, metadata, selection
        self.reader = _Sources(source.parent, metadata)
        self.declared = {}
        self.cache, self.posts, self.groups, self.prompts = {}, {}, {}, {}
        for key in ('inputs', 'prompts', 'answers', 'records', 'parameters',
                    'failed_receipts', 'dependencies'):
            for binding in selection.get(key, []):
                path, digest = binding.get('path'), binding.get('sha256')
                if (not isinstance(path, str) or not isinstance(digest, str)
                        or not re.fullmatch('[0-9a-f]{64}', digest)):
                    raise ValueError('selection requires exact source paths and SHA-256 hashes')
                self.reader.local(path)
                if path in self.declared and self.declared[path] != digest:
                    raise ValueError('conflicting selected source hashes')
                self.declared[path] = digest

    def raw(self, path):
        raw = self.reader.raw(self.reader.local(path), path)
        expected = self.declared.get(path)
        if expected is not None and _sha(raw) != expected:
            raise ValueError('selected source hash does not match: ' + path)
        return raw

    def read(self, path):
        if path not in self.cache:
            self.cache[path] = _json(self.raw(path))
        return self.cache[path]

    def template(self, identity):
        if identity not in self.prompts:
            matches = [p for p in self.selection['prompts'] if p['id'] == identity]
            if len(matches) != 1:
                raise ValueError('call requires exactly one declared prompt template')
            binding = matches[0]
            raw = self.raw(binding['path'])
            text = (_json(raw)[binding['key']]['prompt_template']
                    if 'key' in binding else raw.decode('utf-8'))
            if ('template_sha256' in binding
                    and _sha(text.encode()) != binding['template_sha256']):
                raise ValueError('selected prompt template hash does not match')
            self.prompts[identity] = (text, binding)
        return self.prompts[identity]

    def group(self, call):
        if call['input'] not in {item['path'] for item in self.selection['inputs']}:
            raise ValueError('call input must be explicitly selected')
        source = self.read(call['input'])
        packets = source.get('packets', [source] if 'packet' in source else [])
        matches = [p for p in packets if p['packet'] == call['group']]
        if len(matches) != 1:
            raise ValueError('call requires exactly one source packet')
        packet = matches[0]
        prepared = prepare({'packets': [packet]}, '{NUMBERED_INSTANCES}', [packet['packet']])[0]
        raw_instances = []
        for item in packet['instances']:
            post = dict(type='post', note_id=item['note_id'], text=item['text'])
            previous = self.posts.setdefault(item['note_id'], post)
            if previous != post:
                raise ValueError('one source post ID has conflicting text')
            raw_instances.append({key: item[key] for key in
                ('instance', 'note_id', 'vector_id', 'byte_spans', 'fragments')})
        mode = call['mode']
        if mode == 'exact_mask_deduplicated':
            fragments = {item['instance']: item['fragments'] for item in prepared['instances']}
            instances = [dict(item, fragments=fragments[item['instance']])
                         for item in prepared['sources']]
        elif mode in ('original_order', 'flat_fragments', 'explicit_saved_condition:original',
                      'explicit_saved_condition:restored_hashtags'):
            instances = raw_instances
        else:
            raise ValueError('unsupported declared title input mode: ' + mode)
        supplied = [item['fragments'] for item in instances]
        if mode == 'explicit_saved_condition:restored_hashtags':
            condition_path = call.get('condition_source')
            if condition_path not in self.declared:
                raise ValueError('restored hashtags require their saved condition declaration')
            declaration = self.read(condition_path).get('conditions', {}).get('restored_hashtags')
            expected = []
            for item in instances:
                raw = self.posts[item['note_id']]['text'].encode('utf-8')
                if any(start < 1 or raw[start-1:start] != b'#' for start, end in item['byte_spans']):
                    raise ValueError('saved hashtag condition lacks the original source prefix')
                expected.append(['#'+fragment for fragment in item['fragments']])
            if declaration != expected:
                raise ValueError('saved hashtag condition disagrees with source text')
            supplied = declaration
        value = dict(type='group', group=packet['packet'], mode=mode, instances=instances)
        if mode == 'explicit_saved_condition:restored_hashtags':
            value['supplied_fragments'] = supplied
        digest = _sha(_canonical(value))
        value['input_sha256'] = digest
        self.groups.setdefault(digest, value)
        if mode == 'flat_fragments':
            body = '\n'.join('“'+fragment+'”' for row in supplied for fragment in row)
        else:
            body = '\n'.join(f'{index}. '+ '; '.join('“'+fragment+'”' for fragment in row)
                             for index, row in enumerate(supplied, 1))
        return digest, body

    def answer(self, binding, *, failed=False):
        if failed and Path(binding['path']).name != 'results.jsonl':
            raise ValueError('failed receipt must name results.jsonl')
        output = None if failed else self.read(binding['path'])
        directory = Path(binding['path']).parent
        manifest_path = (directory/'manifest.json').as_posix()
        config_path = (directory.parent/'config.json').as_posix()
        manifest, config = self.read(manifest_path), self.read(config_path)
        if manifest.get('config_sha256') != self.metadata['sources'][config_path]:
            raise ValueError('saved configuration hash does not match its manifest')
        if output is not None and output.get('manifest_sha256') != self.metadata['sources'][manifest_path]:
            raise ValueError('saved output manifest hash does not match')
        prompts = manifest.get('prompts')
        if (not isinstance(prompts, list) or len(prompts) != 1
                or config.get('prompts') != prompts):
            raise ValueError('selected title call requires one bound request and response')
        request = prompts[0]
        input_ref, body = self.group(binding)
        template, prompt_binding = self.template(binding['prompt'])
        marker = '{FRAGMENTS}' if binding['mode'] == 'flat_fragments' else '{NUMBERED_INSTANCES}'
        if template.count(marker) != 1:
            raise ValueError('selected prompt requires exactly one input placeholder')
        expected = template.replace(marker, body)
        actual = request.get('text')
        if (not isinstance(actual, str) or expected.strip() != actual.strip()
                or actual.count(body) != 1):
            raise ValueError('saved request does not match its template and exact source masks')
        used_template = actual.replace(body, marker)
        prompt_ref = _sha(used_template.encode())
        self.metadata['prompts'][prompt_ref] = dict(text=used_template,
            source=prompt_binding['path'], source_sha256=prompt_binding['sha256'],
            version=prompt_binding.get('version', prompt_binding.get('key', 'not_recorded')))
        receipts_path = (directory/'results.jsonl').as_posix()
        receipts = [_json(line) for line in self.raw(receipts_path).splitlines() if line.strip()]
        if not receipts:
            raise ValueError('saved answer has no receipt')
        receipt = receipts[-1]
        if (receipt.get('manifest_sha256') != self.metadata['sources'][manifest_path]
                or receipt.get('prompt_sha256') != _sha(actual.encode())):
            raise ValueError('saved call does not match its receipt')
        if receipt.get('note_id', request['prompt_id']) != request['prompt_id']:
            raise ValueError('saved receipt refers to a different call')
        settings = {key: value for record in (config, manifest, receipt)
                    for key, value in record.items() if key in _SETTINGS}
        settings_ref = _sha(_canonical(settings))
        self.metadata['settings'][settings_ref] = settings
        record = dict(call_id=binding['path'],
            source_path=binding['path'], prompt_id=request['prompt_id'],
            input_ref=input_ref, prompt_ref=prompt_ref,
            version=self.metadata['prompts'][prompt_ref]['version'], settings_ref=settings_ref,
            attempts=len(receipts), request_sha256=_sha(actual.encode()),
            manifest_sha256=self.metadata['sources'][manifest_path])
        if failed:
            if receipt.get('status') != 'failed' or receipt.get('final_output_raw'):
                raise ValueError('selected failed attempt has a different final outcome')
            usage = receipt.get('usage')
            record.update(type='failed_attempt', status='failed', usage=None if usage is None
                else {key: value for key, value in usage.items() if key in {
                    'input_tokens', 'output_tokens', 'cached_input_tokens', 'total_tokens'}})
            return record
        responses = output.get('responses')
        if (not isinstance(responses, list) or len(responses) != 1
                or responses[0].get('prompt_id') != request['prompt_id']
                or not isinstance(responses[0].get('response'), str)):
            raise ValueError('saved answer has a mismatched call identity')
        answer = responses[0]['response']; answer_hash = _sha(answer.encode())
        if (receipt.get('status') != 'succeeded' or receipt.get('final_output_raw') != answer
                or receipt.get('final_output_sha256') != answer_hash):
            raise ValueError('saved final answer does not match its receipt')
        record.update(status='succeeded', output=answer, output_sha256=answer_hash)
        return record


def export_results(source, spec, output=None):
    source = Path(source).expanduser().resolve()
    if not source.is_dir() or spec is None:
        raise ValueError('title study publication requires a source directory and --spec selection')
    spec = Path(spec)
    if spec.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('title study selection exceeds bounded read limit')
    selection_document = _json(spec.read_bytes())
    if selection_document.get('schema_version') != 1:
        raise ValueError('unsupported title study selection schema')
    selection = selection_document.get('studies', {}).get(source.name)
    if not isinstance(selection, dict) or not selection.get('answers'):
        raise ValueError('saved study is not explicitly selected')
    destination = Path(output) if output is not None else source.parent/(source.name+'-publication')
    if destination.is_symlink():
        raise ValueError('publication destination must not be a symlink')
    destination = destination.resolve()
    if source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('publication destination must be outside the saved study')
    metadata = dict(schema_version=1, format=FORMAT, experiment_id=source.name,
        source_id=_sha(_canonical(dict(study=source.name, selection=selection))),
        selection_sha256=_sha(_canonical(selection)), sources={}, prompts={}, settings={},
        exporter_sha256=_sha(Path(__file__).read_bytes()),
        exporter_sources={name: _sha(Path(__file__).with_name(name).read_bytes()) for name in
            ('title_study_publication.py', 'title_study_records.py',
             'prepare_category_title_inputs.py', 'prompt_study_publication.py')},
        AS_status='unknown; retained historical evidence, not current-pipeline validation',
        interpretation='Saved answers and recorded judgments; no new assessment or user approval.')
    with _snapshot(source):
        study = _Study(source, metadata, selection)
        answers = [study.answer(binding) for binding in selection['answers']]
        if len({row['call_id'] for row in answers}) != len(answers):
            raise ValueError('duplicate selected title call')
        dependencies = [study.answer(binding) for binding in selection.get('dependencies', [])]
        metadata['answer_dependencies'] = [
            {key: row[key] for key in ('call_id', 'source_path', 'output_sha256', 'input_ref')}
            for row in dependencies]
        failures = [study.answer(binding, failed=True)
                    for binding in selection.get('failed_receipts', [])]
        context = [dict(row, input_instances=[dict(item,
            text=study.posts[item['note_id']]['text'])
            for item in study.groups[row['input_ref']]['instances']])
            for row in [*answers, *dependencies]]
        records = []
        for binding in [*selection.get('records', []), *selection.get('parameters', [])]:
            value = study.read(binding['path'])
            records.append((binding, value))
        judgments, measurements, parameters = [], [], []
        if records:
            from .title_study_records import project_record
            for binding, value in records:
                role = binding['role']
                projected = project_record(value, role=role, source=binding['path'],
                    answers=context, bindings=metadata['sources'])
                destination_records = (parameters if role == 'study_parameters' else
                    judgments if role.startswith('recorded_') else measurements)
                destination_records.append(projected)
        metadata['parameters'] = parameters

        def results():
            yield from measurements
            yield from failures
            study.reader.check()
            metadata['source_snapshot_sha256'] = _sha(_canonical(metadata['sources']))
            metadata['counts'] = dict(answers=len(answers), inputs=len(study.groups),
                posts=len(study.posts), failed_attempts=len(failures),
                answer_dependencies=len(dependencies), recorded_judgments=len(judgments),
                final_records=len(measurements))

        return shared('publication_files').write_publication(destination, metadata, {
            'inputs.jsonl': [*study.posts.values(), *study.groups.values()],
            'answers.jsonl': answers, 'judgments.jsonl': judgments, 'results.jsonl': results()})
