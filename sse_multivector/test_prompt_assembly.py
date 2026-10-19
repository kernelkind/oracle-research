import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CLI = Path(__file__).with_name('prompt_assembly.py')
PROMPTS = Path(__file__).with_name('shr_single_pair')


def sha256(value):
    return hashlib.sha256(value).hexdigest()


class PromptAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.parts = [b'Instructions\r\n\r\n', 'Shared definition: café.\n'.encode()]
        self.expected = b''.join(self.parts)
        for index, content in enumerate(self.parts):
            (self.root / f'part-{index}.md').write_bytes(content)
        self.destination = self.root / 'Draft-v1.md'
        self.spec = self.root / 'Draft-v1.assembly.json'
        self.manifest = {
            'schema_version': 1,
            'prompt_id': 'Draft-v1',
            'output': {'path': self.destination.name, 'sha256': sha256(self.expected)},
            'parts': [
                {'path': f'part-{index}.md', 'sha256': sha256(content)}
                for index, content in enumerate(self.parts)
            ],
        }
        self.write_spec()

    def write_spec(self):
        self.spec.write_text(json.dumps(self.manifest))

    def invoke(self, command='build', spec=None):
        return subprocess.run(
            [sys.executable, str(CLI), command, str(spec or self.spec)],
            cwd=self.root, capture_output=True, text=True, timeout=10,
        )

    def test_build_preserves_shared_bytes_and_check_reads_the_complete_prompt(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.destination.read_bytes(), self.expected)
        before = self.destination.stat().st_mtime_ns
        for command in ('check', 'build'):
            result = self.invoke(command)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.destination.stat().st_mtime_ns, before)

    def test_changed_or_missing_component_fails_before_creating_output(self):
        for mutation in ('changed', 'missing'):
            with self.subTest(mutation=mutation):
                part = self.root / 'part-1.md'
                if mutation == 'changed':
                    part.write_bytes(b'Unversioned change')
                else:
                    part.unlink()
                result = self.invoke()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('part-1.md', result.stderr)
                self.assertFalse(self.destination.exists())
                part.write_bytes(self.parts[1])

    def test_wrong_output_hash_fails_before_creating_output(self):
        self.manifest['output']['sha256'] = '0' * 64
        self.write_spec()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('assembled prompt SHA-256', result.stderr)
        self.assertFalse(self.destination.exists())

    def test_literal_separators_preserve_layout_without_extra_source_files(self):
        separator = '\n\n'
        self.manifest['parts'].insert(1, {'text': separator})
        expected = self.parts[0] + separator.encode() + self.parts[1]
        self.manifest['output']['sha256'] = sha256(expected)
        self.write_spec()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.destination.read_bytes(), expected)
        self.assertEqual(self.invoke('check').returncode, 0)

    def test_invalid_literal_text_fails_before_creating_output(self):
        self.manifest['parts'].insert(1, {'text': 42})
        self.write_spec()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('literal prompt text must be a string', result.stderr)
        self.assertFalse(self.destination.exists())

    def test_existing_prompt_is_never_overwritten(self):
        self.destination.write_bytes(b'Existing frozen version')
        for command in ('build', 'check'):
            result = self.invoke(command)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('differs', result.stderr)
            self.assertEqual(self.destination.read_bytes(), b'Existing frozen version')

    def paired_specs(self):
        shared = {'path': 'part-1.md', 'sha256': sha256(self.parts[1])}
        companion = self.root / 'Partner-v1.assembly.json'
        other = {**self.manifest, 'prompt_id': 'Partner-v1',
                 'output': {'path': 'Partner-v1.md', 'sha256': sha256(self.expected)},
                 'shared': shared, 'companion': self.spec.name}
        self.manifest.update(shared=shared, companion=companion.name)
        self.write_spec()
        companion.write_text(json.dumps(other))
        return companion

    def test_paired_assembly_rejects_different_shared_rules_before_writing(self):
        companion = self.paired_specs()
        other = json.loads(companion.read_text())
        alternate = b'Different shared rules\n'
        (self.root / 'alternate.md').write_bytes(alternate)
        other['shared'] = {'path': 'alternate.md', 'sha256': sha256(alternate)}
        other['parts'][1] = other['shared']
        other['output']['sha256'] = sha256(self.parts[0] + alternate)
        companion.write_text(json.dumps(other))
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('shared rules differ', result.stderr)
        self.assertFalse(self.destination.exists())

    def test_sync_publishes_both_versions_and_preserves_old_prompts(self):
        companion = self.paired_specs()
        self.assertEqual(self.invoke().returncode, 0)
        self.assertEqual(self.invoke(spec=companion).returncode, 0)
        original = {p: p.read_bytes() for p in (
            self.spec, companion, self.destination, self.root / 'Partner-v1.md')}
        rules = self.root / 'rules-v2.md'
        rules.write_bytes(b'Updated shared definition rules.\n')
        result = subprocess.run([
            sys.executable, str(CLI), 'sync', str(self.spec),
            '--rules', str(rules), '--prompt-id', 'Draft-v2',
            '--companion-id', 'Partner-v2'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for identifier in ('Draft-v2', 'Partner-v2'):
            new_spec = self.root / (identifier + '.assembly.json')
            self.assertEqual(self.invoke('check', new_spec).returncode, 0)
            self.assertEqual((self.root / (identifier + '.md')).read_bytes(),
                             self.parts[0] + rules.read_bytes())
            self.assertEqual(json.loads(new_spec.read_text())['shared'],
                             {'path': 'rules-v2.md', 'sha256': sha256(rules.read_bytes())})
        self.assertEqual({p: p.read_bytes() for p in original}, original)

    def test_sync_refuses_collision_without_partial_publication(self):
        companion = self.paired_specs()
        self.assertEqual(self.invoke().returncode, 0)
        self.assertEqual(self.invoke(spec=companion).returncode, 0)
        rules = self.root / 'rules-v2.md'
        rules.write_bytes(b'Updated shared definition rules.\n')
        existing = self.root / 'Partner-v2.md'
        existing.write_bytes(b'Already frozen\n')
        result = subprocess.run([
            sys.executable, str(CLI), 'sync', str(self.spec),
            '--rules', str(rules), '--prompt-id', 'Draft-v2',
            '--companion-id', 'Partner-v2'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('already exists', result.stderr)
        self.assertFalse((self.root / 'Draft-v2.md').exists())
        self.assertFalse((self.root / 'Draft-v2.assembly.json').exists())
        self.assertEqual(existing.read_bytes(), b'Already frozen\n')

    def test_sync_rolls_back_failed_pair_validation(self):
        companion = self.paired_specs()
        self.assertEqual(self.invoke().returncode, 0)
        self.assertEqual(self.invoke(spec=companion).returncode, 0)
        rules = self.root / 'rules-v2.md'
        # This appears in the wrapper already, violating single inclusion.
        rules.write_bytes(self.parts[0])
        result = subprocess.run([
            sys.executable, str(CLI), 'sync', str(self.spec),
            '--rules', str(rules), '--prompt-id', 'Draft-v2',
            '--companion-id', 'Partner-v2'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exactly once', result.stderr)
        for identifier in ('Draft-v2', 'Partner-v2'):
            self.assertFalse((self.root / (identifier + '.md')).exists())
            self.assertFalse((self.root / (identifier + '.assembly.json')).exists())

    def test_future_bootstrap_and_consolidation_versions_have_matching_shared_rules(self):
        initial = [PROMPTS / 'Hierarchy-bootstrap-v129.assembly.json',
                   PROMPTS / 'Hierarchy-consolidation-v21.assembly.json']
        for path in initial:
            self.assertTrue(path.exists(), str(path))
        for family, first_version in (('bootstrap', 129), ('consolidation', 21)):
            for prompt in PROMPTS.glob(f'Hierarchy-{family}-v*.md'):
                version = int(prompt.stem.rsplit('-v', 1)[1])
                if version < first_version:
                    continue
                manifest = prompt.with_suffix('.assembly.json')
                self.assertTrue(manifest.exists(), f'Publish {prompt.name} with paired assembly')
                spec = json.loads(manifest.read_text())
                self.assertIn('shared', spec)
                self.assertIn('companion', spec)
                self.assertEqual(self.invoke('check', manifest).returncode, 0)
        fragment = (PROMPTS / 'prompt_parts/explicit-meaning-rules-v6.md').read_bytes()
        self.assertNotIn(b'resolutions', fragment)
        self.assertNotIn(b'null meaning', fragment)
        for identifier in ('Hierarchy-bootstrap-v129', 'Hierarchy-consolidation-v21'):
            self.assertEqual((PROMPTS / (identifier + '.md')).read_bytes().count(fragment), 1)
        self.assertEqual(sha256((PROMPTS / 'Hierarchy-bootstrap-v126.md').read_bytes()),
                         '85dbf0b23de1dd085cdd7519650d0e9bcf9bd7264e4d517b1a1f461c436e3f30')
        self.assertEqual(sha256((PROMPTS / 'Hierarchy-consolidation-v20.md').read_bytes()),
                         '07b87f7f54ca079564228c067a40f7ec3655388763aa4796bdd7bbbff79a21be')

    def test_bootstrap_title_examples_validate_with_native_schema(self):
        from sse_multivector import experiment_inputs

        schema = json.loads((PROMPTS / 'Hierarchy-bootstrap-v130.output.schema.json').read_text())
        example_pattern = (r'<example>\s*<input>\s*(.*?)\s*</input>\s*'
                           r'<output>\s*(.*?)\s*</output>\s*</example>')
        original_examples = re.findall(example_pattern,
                                       (PROMPTS / 'Hierarchy-bootstrap-v129.md').read_text(), re.S)
        for version in (130, 131, 132, 133, 134, 135):
            with self.subTest(version=version):
                prompt = (PROMPTS / f'Hierarchy-bootstrap-v{version}.md').read_text()
                examples = re.findall(example_pattern, prompt, re.S)
                self.assertEqual(len(examples), 2)
                for (input_json, output), (original_input, original_output) in zip(
                        examples, original_examples, strict=True):
                    self.assertEqual(input_json, original_input)
                    case = {'inputs': {'INPUT_JSON': input_json}}
                    value = experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'},
                                                       case, output, schema)['parsed']
                    self.assertIsInstance(value['title'], str)
                    expected = json.loads(original_output)
                    if version >= 135 and value['title'] == 'Feedback':
                        expected['meaning'] = (
                            'Feedback consists of views, evaluations or suggestions '
                            'communicated about an activity or experience.')
                    self.assertEqual({key: field for key, field in value.items() if key != 'title'},
                                     expected)
        historical = (PROMPTS / 'Hierarchy-bootstrap-v129.md').read_bytes()
        self.assertEqual(sha256(historical),
                         '1ea170044a0daf63916e576df68e932b50ade5b3f8adec6a47fae5a420e8765e')

    def test_general_category_example_uses_native_validation_and_preserves_prior_examples(self):
        from sse_multivector import experiment_inputs

        pattern = (r'<example>\s*<input>\s*(.*?)\s*</input>\s*'
                   r'<output>\s*(.*?)\s*</output>\s*</example>')
        previous = re.findall(pattern, (PROMPTS / 'Hierarchy-bootstrap-v135.md').read_text(), re.S)
        schema = json.loads((PROMPTS / 'Hierarchy-bootstrap-v130.output.schema.json').read_text())
        for version, title, meaning in (
                (136, 'Birds', 'Birds are feathered vertebrate animals.'),
                (137, 'Transportation',
                 'Transportation is the movement of people or goods from one place to another.'),
                (138, 'Transportation',
                 'Transportation is the movement of people or goods from one place to another.')):
            with self.subTest(version=version):
                examples = re.findall(
                    pattern, (PROMPTS / f'Hierarchy-bootstrap-v{version}.md').read_text(), re.S)
                self.assertEqual(len(examples), 3)
                self.assertEqual(examples[:2], previous)
                for input_json, output in examples:
                    value = experiment_inputs.validate(
                        {'adapter': 'hierarchy_local_nodes'},
                        {'inputs': {'INPUT_JSON': input_json}}, output, schema)['parsed']
                self.assertEqual(value['meaning'], meaning)
                self.assertEqual(value['title'], title)

    def test_composition_example_uses_native_validation_and_preserves_prior_examples(self):
        from sse_multivector import experiment_inputs

        pattern = (r'<example>\s*<input>\s*(.*?)\s*</input>\s*'
                   r'<output>\s*(.*?)\s*</output>\s*</example>')
        examples = re.findall(pattern, (PROMPTS / 'Hierarchy-bootstrap-v139.md').read_text(), re.S)
        previous = re.findall(pattern, (PROMPTS / 'Hierarchy-bootstrap-v138.md').read_text(), re.S)
        self.assertEqual(len(examples), 4)
        self.assertEqual(examples[:3], previous)
        schema = json.loads((PROMPTS / 'Hierarchy-bootstrap-v130.output.schema.json').read_text())
        for input_json, output in examples:
            value = experiment_inputs.validate(
                {'adapter': 'hierarchy_local_nodes'},
                {'inputs': {'INPUT_JSON': input_json}}, output, schema)['parsed']
        self.assertEqual(value['meaning'],
                         '18-karat gold is a gold alloy with a nominal gold content of 75% by mass.')
        self.assertEqual(value['title'], '18-karat gold')

    def test_topic_name_revision_preserves_meanings_and_validates_examples(self):
        from sse_multivector import experiment_inputs
        from sse_multivector.prompt_assembly import compile_spec

        old, _, old_prompt = compile_spec(PROMPTS / 'Hierarchy-bootstrap-v139.assembly.json')
        pattern = (r'<example>\s*<input>\s*(.*?)\s*</input>\s*'
                   r'<output>\s*(.*?)\s*</output>\s*</example>')
        previous = re.findall(pattern, old_prompt.decode(), re.S)
        schema = json.loads((PROMPTS / 'Hierarchy-bootstrap-v130.output.schema.json').read_text())
        for version in (140, 141, 142, 143, 144, 145, 146, 147):
            with self.subTest(version=version):
                new, _, new_prompt = compile_spec(
                    PROMPTS / f'Hierarchy-bootstrap-v{version}.assembly.json')
                self.assertEqual(new['shared'], old['shared'])
                self.assertEqual(new['companion'], old['companion'])
                current = re.findall(pattern, new_prompt.decode(), re.S)
                self.assertEqual(len(current), 4)
                for index, ((input_json, output), (old_input, old_output)) in enumerate(
                        zip(current, previous, strict=True)):
                    self.assertEqual(input_json, old_input)
                    value = experiment_inputs.validate(
                        {'adapter': 'hierarchy_local_nodes'},
                        {'inputs': {'INPUT_JSON': input_json}}, output, schema)['parsed']
                    expected = json.loads(old_output)
                    self.assertEqual({k: v for k, v in value.items() if k != 'title'},
                                     {k: v for k, v in expected.items() if k != 'title'})
                    self.assertEqual(value['title'], 'Studio portrait negatives' if index == 1
                                     else expected['title'])

    def test_scope_revision_preserves_example_outputs_and_synchronizes_rules(self):
        from sse_multivector import experiment_inputs
        from sse_multivector.prompt_assembly import compile_spec, paired_spec

        original, _, old_prompt = compile_spec(PROMPTS / 'Hierarchy-bootstrap-v147.assembly.json')
        pattern = (r'<example>\s*<input>\s*(.*?)\s*</input>\s*'
                   r'<output>\s*(.*?)\s*</output>\s*</example>')
        old_examples = re.findall(pattern, old_prompt.decode(), re.S)
        schema = json.loads((PROMPTS / 'Hierarchy-bootstrap-v130.output.schema.json').read_text())
        for version in (148, 149, 150):
            with self.subTest(version=version):
                path = PROMPTS / f'Hierarchy-bootstrap-v{version}.assembly.json'
                current, _, prompt = compile_spec(path)
                _, companion, _, _ = paired_spec(path.resolve(), current)
                self.assertEqual(current['shared'], companion['shared'])
                self.assertNotEqual(current['shared'], original['shared'])
                self.assertEqual(self.invoke('check', path).returncode, 0)
                examples = re.findall(pattern, prompt.decode(), re.S)
                self.assertEqual(len(examples), len(old_examples))
                for index, ((input_json, output), (old_input, old_output)) in enumerate(
                        zip(examples, old_examples, strict=True)):
                    value = experiment_inputs.validate(
                        {'adapter': 'hierarchy_local_nodes'},
                        {'inputs': {'INPUT_JSON': input_json}}, output, schema)['parsed']
                    if version == 150 and index == 2:
                        self.assertEqual(value['meaning'],
                            'Transportation of fragile goods is moving goods that are easily damaged '
                            'from one place to another.')
                        self.assertEqual(value['title'], 'Fragile goods transportation')
                        continue
                    expected_input = json.loads(old_input)
                    if version == 149 and index == 2:
                        expected_input['local']['hierarchy']['entries'][0]['subject'] = (
                            'Transportation, including bus and train services')
                    self.assertEqual(json.loads(input_json), expected_input)
                    self.assertEqual(value, json.loads(old_output))

    def test_definition_only_pair_preserves_wrappers_and_changes_shared_rules_together(self):
        from sse_multivector.prompt_assembly import compile_spec

        for family, current, previous in (('bootstrap', 134, 133), ('consolidation', 22, 21),
                                          ('bootstrap', 138, 137), ('consolidation', 26, 25),
                                          ('bootstrap', 148, 147), ('consolidation', 28, 27)):
            with self.subTest(family=family):
                path = PROMPTS / f'Hierarchy-{family}-v{current}.assembly.json'
                spec, _, content = compile_spec(path)
                old, _, old_content = compile_spec(
                    PROMPTS / f'Hierarchy-{family}-v{previous}.assembly.json')
                self.assertEqual(self.invoke('check', path).returncode, 0)
                rules = (PROMPTS / spec['shared']['path']).read_bytes()
                old_rules = (PROMPTS / old['shared']['path']).read_bytes()
                self.assertNotEqual(rules, old_rules)
                self.assertEqual(content, old_content.replace(old_rules, rules))
                peer = json.loads((PROMPTS / spec['companion']).read_text())
                self.assertEqual(peer['shared'], spec['shared'])
                self.assertEqual(peer['companion'], path.name)

    def test_manifest_rejects_unversioned_output_and_output_as_its_own_source(self):
        self.manifest['output']['path'] = 'different-name.md'
        self.write_spec()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('prompt_id', result.stderr)
        self.manifest['output']['path'] = self.destination.name
        self.manifest['parts'][0]['path'] = self.destination.name
        self.write_spec()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('own source', result.stderr)

    def test_real_prompts_share_exact_rules_and_bootstrap_bytes_are_preserved(self):
        fragment = (PROMPTS / 'prompt_parts' / 'explicit-meaning-rules-v1.md').read_bytes()
        for version in ('Hierarchy-bootstrap-v104', 'Hierarchy-consolidation-v1'):
            spec = PROMPTS / f'{version}.assembly.json'
            with self.subTest(version=version):
                result = self.invoke('check', spec)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = json.loads(spec.read_text())
                self.assertEqual(sum(p['path'].endswith('explicit-meaning-rules-v1.md')
                                     for p in manifest['parts']), 1)
                prompt = (PROMPTS / f'{version}.md').read_bytes()
                self.assertEqual(prompt.count(fragment), 1)
        bootstrap = (PROMPTS / 'Hierarchy-bootstrap-v104.md').read_bytes()
        self.assertEqual(sha256(bootstrap),
                         'd97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0')

    def test_expanded_rules_are_shared_with_the_unchanged_bootstrap_reference(self):
        for name in ('Hierarchy-consolidation-v2.assembly.json',
                     'Hierarchy-bootstrap-v104.shared-v2.assembly.json'):
            result = self.invoke('check', PROMPTS / name)
            self.assertEqual(result.returncode, 0, result.stderr)
        specs = [json.loads((PROMPTS / name).read_text()) for name in (
            'Hierarchy-consolidation-v2.assembly.json',
            'Hierarchy-bootstrap-v104.shared-v2.assembly.json')]
        shared_parts = [[p for p in s['parts'] if '/explicit-meaning-rules-v2/' in p.get('path', '')]
                        for s in specs]
        self.assertEqual(shared_parts[0], shared_parts[1])
        bootstrap = (PROMPTS / 'Hierarchy-bootstrap-v104.md').read_bytes()
        consolidation = (PROMPTS / 'Hierarchy-consolidation-v2.md').read_bytes()
        shared = []
        for part in shared_parts[0]:
            text = (PROMPTS / part['path']).read_bytes()
            self.assertEqual(bootstrap.count(text), 1)
            self.assertEqual(consolidation.count(text), 1)
            shared.append(text)
        rules = b'\n'.join(shared)
        for instruction in (
            b'Retain the selected name to preserve identity.',
            b'Do not discard an alternative or part',
            b'Distinguish defining features from optional variations.',
            b'required actions, methods, roles, purposes or states',
            b'"typically" or "usually"',
            b'Apply each chosen restriction consistently',
            b'choices cannot form one coherent meaning, return a null meaning.',
        ):
            self.assertIn(instruction, rules)
        self.assertNotIn(b'resolutions', rules)
        self.assertEqual(sha256(bootstrap),
                         'd97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0')
        self.assertEqual(sha256((PROMPTS / 'Hierarchy-consolidation-v1.md').read_bytes()),
                         '6a93d4d2a06c20b3a46ffd9758144cd280f7f0017153eb18a43cae72b2947965')

    def test_parent_only_consolidation_preserves_shared_rules(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v3.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v2.assembly.json').read_text())
        current = json.loads(spec.read_text())
        self.assertEqual(previous['parts'][1:], current['parts'][1:])
        prompt = (PROMPTS / 'Hierarchy-consolidation-v3.md').read_text()
        self.assertNotIn('ancestor', prompt)
        self.assertNotIn('`parents`', prompt)
        self.assertIn('must be narrower than its fixed meaning.', prompt)

    def test_consolidation_v4_preserves_shared_rules_and_approved_baseline(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v4.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v3.assembly.json').read_text())
        current = json.loads(spec.read_text())
        self.assertEqual(previous['parts'][1:-1], current['parts'][1:-1])
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        self.assertEqual(sha256(baseline.read_bytes()),
                         'da792812ee72c958df9b1fc1e5c8792a8c2172ded90eff52862e17f3939d8990')
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v4.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_v5_preserves_shared_rules_and_approved_baseline(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v5.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        for version in ('v3', 'v4'):
            previous = json.loads((PROMPTS / f'Hierarchy-consolidation-{version}.assembly.json').read_text())
            self.assertEqual(previous['parts'][1:-1], current['parts'][1:-1])
            self.assertEqual(sha256((PROMPTS / previous['output']['path']).read_bytes()),
                             previous['output']['sha256'])
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v5.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_v6_preserves_shared_rules_and_approved_baseline(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v6.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v5.assembly.json').read_text())
        self.assertEqual(previous['parts'][:-1], current['parts'][:-1])
        self.assertEqual(sha256((PROMPTS / previous['output']['path']).read_bytes()),
                         previous['output']['sha256'])
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v6.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_v7_preserves_shared_rules_and_approved_baseline(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v7.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v6.assembly.json').read_text())
        self.assertEqual(previous['parts'][:-1], current['parts'][:-1])
        self.assertEqual(sha256((PROMPTS / previous['output']['path']).read_bytes()),
                         previous['output']['sha256'])
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v7.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_v8_separates_null_behavior_and_preserves_shared_writing(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v8.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v7.assembly.json').read_text())
        self.assertEqual(previous['parts'][1:-2], current['parts'][1:-2])
        previous_consistency = (PROMPTS / previous['parts'][-2]['path']).read_bytes()
        shared_consistency = (PROMPTS / current['parts'][-2]['path']).read_bytes()
        self.assertEqual(shared_consistency, previous_consistency.partition(
            b' If a material ambiguity remains unresolved')[0])
        bootstrap = (PROMPTS / 'Hierarchy-bootstrap-v104.md').read_bytes()
        prompt = (PROMPTS / current['output']['path']).read_bytes()
        self.assertEqual(bootstrap.count(shared_consistency), 1)
        self.assertEqual(prompt.count(shared_consistency), 1)
        self.assertEqual(sha256(bootstrap),
                         'd97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0')
        self.assertEqual(sha256((PROMPTS / previous['output']['path']).read_bytes()),
                         previous['output']['sha256'])
        self.assertNotIn(b'return a null meaning', prompt)
        self.assertNotIn(b'# Check the siblings', prompt)
        self.assertNotIn(b'They may have any color.', prompt)
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v8.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_v9_pins_simplified_writing_without_changing_prior_prompts(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v9.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        shared = [part for part in current['parts']
                  if 'prompt_parts/' in part.get('path', '')]
        self.assertEqual(len(shared), 1)
        shared_text = (PROMPTS / shared[0]['path']).read_bytes()
        prompt = (PROMPTS / current['output']['path']).read_bytes()
        self.assertEqual(prompt.count(shared_text), 1)
        previous = (PROMPTS / 'Hierarchy-consolidation-v8.md').read_bytes()
        self.assertEqual(prompt.split(b'\n# Check the proposal\n', 1)[1],
                         previous.split(b'\n# Check the proposal\n', 1)[1])
        self.assertEqual(sha256(previous),
                         '5bb245a302a18f3e34bee56636509bfa221b1930a8f88e57ed2b8bee8fde7b42')
        self.assertEqual(sha256((PROMPTS / 'Hierarchy-bootstrap-v104.md').read_bytes()),
                         'd97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0')
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v9.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_v10_restores_only_the_topic_definition_rule(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v10.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v9.assembly.json').read_text())
        self.assertEqual(current['parts'][:2], previous['parts'][:2])
        self.assertEqual(current['parts'][3:], previous['parts'][3:])
        old_shared = (PROMPTS / previous['parts'][2]['path']).read_bytes()
        new_shared = (PROMPTS / current['parts'][2]['path']).read_bytes()
        insertion = b' Define the selected topic, not every concept it mentions.'
        self.assertEqual(new_shared.count(insertion), 1)
        self.assertEqual(new_shared.replace(insertion, b''), old_shared)
        prompt = (PROMPTS / current['output']['path']).read_bytes()
        old_prompt = (PROMPTS / previous['output']['path']).read_bytes()
        self.assertEqual(prompt.count(new_shared), 1)
        self.assertEqual(prompt.replace(insertion, b''), old_prompt)
        self.assertEqual(sha256(old_prompt),
                         '751c9d83c43fa69ca1f57042a95cc5574eed8a556e57b1547c4bb38b9baf6beb')
        self.assertEqual(sha256((PROMPTS / 'Hierarchy-bootstrap-v104.md').read_bytes()),
                         'd97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0')
        baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v10.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
        self.assertEqual(Path(revision['base_path']).name, baseline.name)
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_consolidation_revisions_preserve_shared_writing_and_the_output_contract(self):
        for version, previous_version, previous_hash in (
            ('v11', 'v10', '53cc0c8d4aa71db22408da13b60958a141d07cadc3df46cd43e1458e0f5cc452'),
            ('v13', 'v11', 'e388dca5ff6d498f29b3fd0051d7af77922344b20e61ed01796ebb20d3419461'),
            ('v14', 'v13', 'baa849577fdfd0f9b46f035192681e8d8dca4db6163bc2b1ed430a33b946e644'),
            ('v15', 'v14', '514630345cf469ec79b41573b37d9e50414c8cbce0803c3dc6de54370493d377'),
            ('v16', 'v15', '89ada99a213be8637c6fce916f6a5d4da22abfa199978ce0ce9af1e6e58b6249'),
            ('v17', 'v16', '9e44bae31b2b577097791ea77c2e4af0f737dd092340e8f5bb3158a52132afab'),
            ('v18', 'v17', '877fc2885d36f2c2b2b47027f5e73550febb4c2119f94992d7c011cc1beb03fd'),
        ):
            with self.subTest(version=version):
                spec = PROMPTS / f'Hierarchy-consolidation-{version}.assembly.json'
                result = self.invoke('check', spec)
                self.assertEqual(result.returncode, 0, result.stderr)
                current = json.loads(spec.read_text())
                previous = json.loads((PROMPTS / f'Hierarchy-consolidation-{previous_version}.assembly.json').read_text())
                self.assertEqual(current['parts'][:-1], previous['parts'][:-1])
                prompt = (PROMPTS / current['output']['path']).read_bytes()
                old_prompt = (PROMPTS / previous['output']['path']).read_bytes()
                boundary = b'\n# Check the proposal\n'
                self.assertEqual(prompt.split(boundary, 1)[0], old_prompt.split(boundary, 1)[0])
                example = b'\n# Synthetic example\n'
                if version in ('v15', 'v16'):
                    self.assertEqual(prompt.split(example, 1)[0], old_prompt.split(example, 1)[0])
                    output = b'\n# Output\n'
                    self.assertEqual(prompt.split(output, 1)[1], old_prompt.split(output, 1)[1])
                else:
                    self.assertEqual(prompt.split(example, 1)[1], old_prompt.split(example, 1)[1])
                if version == 'v17':
                    self.assertNotIn(b'or its topic identity', prompt)
                    self.assertIn(b'a node\'s title, customary uses, association or existing placement', prompt)
                    self.assertIn(b'Exclude a sibling only when its fixed meaning admits information outside the proposed meaning.', prompt)
                if version == 'v18':
                    audit = (PROMPTS / 'Hierarchy-consolidation-audit-v5.md').read_bytes()
                    coverage = b'Include a sibling only when '
                    self.assertEqual(
                        prompt.split(coverage, 1)[1].split(b'\n\n`children`', 1)[0],
                        audit.split(coverage, 1)[1].split(b'\n\n# Output', 1)[0])
                    self.assertEqual(audit.split(b'\n# Output\n', 1)[1],
                        (PROMPTS / 'Hierarchy-consolidation-audit-v4.md').read_bytes()
                            .split(b'\n# Output\n', 1)[1])
                shared = (PROMPTS / current['parts'][2]['path']).read_bytes()
                self.assertEqual(prompt.count(shared), 1)
                self.assertEqual(sha256(old_prompt), previous_hash)
                self.assertEqual(sha256((PROMPTS / 'Hierarchy-bootstrap-v104.md').read_bytes()),
                                 'd97d0cfe078546e9525ac15252b81eee20630fba6e4786b1000c5cf942d49ba0')
                baseline = PROMPTS / 'Hierarchy-consolidation-v3.md'
                revision = json.loads((PROMPTS / f'Hierarchy-consolidation-{version}.md.revision.json').read_text())
                self.assertEqual(revision['base_sha256'], sha256(baseline.read_bytes()))
                self.assertEqual(Path(revision['base_path']).name, baseline.name)
                self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_counterexample_revision_preserves_other_prompt_sections(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v19.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v18.assembly.json').read_text())
        self.assertEqual(current['parts'][:-1], previous['parts'][:-1])
        prompt = (PROMPTS / current['output']['path']).read_bytes()
        old_prompt = (PROMPTS / previous['output']['path']).read_bytes()
        begin = b'\n# Identify the children\n'
        end = b'\n\n`children` must contain'
        self.assertEqual(prompt.split(begin, 1)[0], old_prompt.split(begin, 1)[0])
        self.assertEqual(prompt.split(end, 1)[1], old_prompt.split(end, 1)[1])
        check = prompt.split(begin, 1)[1].split(end, 1)[0]
        self.assertIn(b'look for a case admitted by its fixed meaning', check)
        self.assertIn(b'Check that the case satisfies the sibling', check)
        self.assertIn(b'failure to find a counterexample alone does not establish coverage', check)
        self.assertEqual(check.count(b'If such a case is possible, exclude that sibling.'), 1)
        self.assertNotIn(b'Exclude a sibling if its meaning allows a case outside', check)
        self.assertEqual(sha256(old_prompt),
                         '3d01c0854762ca6e4baa8fe752fd1b409334cfb874a360da61543e38c0bdf9fd')
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v19.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256((PROMPTS / 'Hierarchy-consolidation-v3.md').read_bytes()))
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_sibling_scope_revision_preserves_shared_rules_and_other_checks(self):
        spec = PROMPTS / 'Hierarchy-consolidation-v20.assembly.json'
        result = self.invoke('check', spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        current = json.loads(spec.read_text())
        previous = json.loads((PROMPTS / 'Hierarchy-consolidation-v19.assembly.json').read_text())
        self.assertEqual(current['parts'][:-1], previous['parts'][:-1])
        prompt = (PROMPTS / current['output']['path']).read_bytes()
        old_prompt = (PROMPTS / previous['output']['path']).read_bytes()
        old = b"A required consumer, purpose, role or state must follow from the sibling's fixed meaning or its necessary implications; illustrative examples and conventional associations cannot supply it. Include all siblings meeting these conditions. Apply any stated coverage of associated activities, products or participants."
        before, after = old_prompt.split(old)
        self.assertTrue(prompt.startswith(before))
        self.assertTrue(prompt.endswith(after))
        changed = prompt[len(before):-len(after)]
        self.assertIn(b'A restriction stated by one sibling does not restrict another sibling.', changed)
        self.assertIn(b'either retain it and exclude the others, or choose a coherent broader meaning', changed)
        self.assertIn(b'recheck every sibling against that final meaning', changed)
        self.assertIn(b'Apply each condition to the kind or relationship it qualifies.', changed)
        shared = (PROMPTS / current['parts'][2]['path']).read_bytes()
        self.assertEqual(prompt.count(shared), 1)
        self.assertEqual(sha256(old_prompt),
                         '4abab9a5dad919537fdf47b05e20cca1ee66ec52955a7d79ae8f741803da6303')
        revision = json.loads((PROMPTS / 'Hierarchy-consolidation-v20.md.revision.json').read_text())
        self.assertEqual(revision['base_sha256'], sha256((PROMPTS / 'Hierarchy-consolidation-v3.md').read_bytes()))
        self.assertEqual(revision['prompt_sha256'], current['output']['sha256'])

    def test_shared_runner_freezes_the_complete_assembled_prompt_without_inference(self):
        runner_root = CLI.resolve().parents[2] / 'experiment-runner'
        launcher = runner_root / 'bin' / 'experiment-runner'
        call_log = self.root / 'calls.json'
        cases = self.root / 'cases.json'
        data = {'parent': None, 'ancestors': [], 'siblings': [
            {'id': 'C1', 'title': 'Coffee', 'meaning': 'Brewed coffee beverages.'},
            {'id': 'C2', 'title': 'Tea', 'meaning': 'Tea beverages.'},
            {'id': 'C3', 'title': 'Gardening', 'meaning': 'Cultivating plants in a garden.'},
        ]}
        for version in ('Hierarchy-consolidation-v1', 'Hierarchy-consolidation-v2',
                        'Hierarchy-consolidation-v3', 'Hierarchy-consolidation-v4',
                        'Hierarchy-consolidation-v5', 'Hierarchy-consolidation-v6',
                        'Hierarchy-consolidation-v7', 'Hierarchy-consolidation-v8',
                        'Hierarchy-consolidation-v9', 'Hierarchy-consolidation-v10',
                        'Hierarchy-consolidation-v11', 'Hierarchy-consolidation-v12',
                        'Hierarchy-consolidation-v13', 'Hierarchy-consolidation-v14',
                        'Hierarchy-consolidation-v15', 'Hierarchy-consolidation-v16',
                        'Hierarchy-consolidation-v17', 'Hierarchy-consolidation-v18',
                        'Hierarchy-consolidation-v19', 'Hierarchy-consolidation-v20',
                        'Hierarchy-consolidation-v21', 'Hierarchy-bootstrap-v129'):
            with self.subTest(version=version):
                inputs = json.dumps({key: value for key, value in data.items()
                                     if version not in ('Hierarchy-consolidation-v3', 'Hierarchy-consolidation-v4',
                                                        'Hierarchy-consolidation-v5', 'Hierarchy-consolidation-v6',
                                                        'Hierarchy-consolidation-v7', 'Hierarchy-consolidation-v8',
                                                        'Hierarchy-consolidation-v9', 'Hierarchy-consolidation-v10',
                                                        'Hierarchy-consolidation-v11', 'Hierarchy-consolidation-v12',
                                                        'Hierarchy-consolidation-v13', 'Hierarchy-consolidation-v14',
                                                        'Hierarchy-consolidation-v15', 'Hierarchy-consolidation-v16',
                                                        'Hierarchy-consolidation-v17', 'Hierarchy-consolidation-v18')
                                     or key != 'ancestors'})
                cases.write_text(json.dumps({'cases': [{'id': 'roots', 'inputs': {'INPUT_JSON': inputs}}]}))
                spec = self.root / (version + '.spec.json')
                prompt = PROMPTS / (version + '.md')
                spec.write_text(json.dumps({
                    'schema_version': 1,
                    'prompt': {'id': version, 'path': str(prompt)},
                    'dataset': {'adapter': 'generic', 'path': str(cases)},
                    'runner': {'provider': 'openai-codex', 'model': 'fixture/model',
                               'reasoning_effort': 'off',
                               'runner_binary': str(runner_root / 'tests/fixtures/fake-runner.py')},
                }))
                destination = self.root / ('prepared-' + version)
                result = subprocess.run(
                    [str(launcher), 'prepare', str(destination), '--spec', str(spec)],
                    cwd=self.root, env={**os.environ, 'FAKE_RUNNER_LOG': str(call_log)},
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(call_log.exists(), 'preparation must not run inference')
                plan = json.loads((destination / 'experiment.json').read_text())['plan']
                self.assertEqual(plan['prompt']['text'], prompt.read_bytes().decode())
                self.assertEqual(plan['cases'][0]['prompt'],
                                 prompt.read_bytes().decode().replace('{INPUT_JSON}', inputs))


if __name__ == '__main__':
    unittest.main()
