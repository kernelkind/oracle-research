import hashlib
import json
import os
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
                        'Hierarchy-consolidation-v5'):
            with self.subTest(version=version):
                inputs = json.dumps({key: value for key, value in data.items()
                                     if version not in ('Hierarchy-consolidation-v3', 'Hierarchy-consolidation-v4',
                                                        'Hierarchy-consolidation-v5')
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
