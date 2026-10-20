"""Preparation provenance through the production projection and real Git repos."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class HierarchyPublicationProvenanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.oracle = self.root / 'oracle-mvp'
        self.runner = self.root / 'experiment-runner'
        source = Path(__file__).with_name('hierarchy_publication_provenance.py')
        self.assertTrue(source.exists(), 'production preparation provenance is missing')
        for repository, files in (
            (self.oracle, {'sse_multivector/generation.py': 'value = 1\n',
                           'sse_multivector/test_example.py': 'pass\n',
                           'README.md': 'Documentation\n'}),
            (self.runner, {'experiment_runner/experiment.py': 'value = 1\n',
                           'tests/test_example.py': 'pass\n',
                           'README.md': 'Documentation\n'}),
        ):
            repository.mkdir()
            self.git(repository, 'init', '--quiet')
            self.git(repository, 'config', 'user.name', 'Fixture')
            self.git(repository, 'config', 'user.email', 'fixture@example.invalid')
            for relative, content in files.items():
                path = repository / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        copied = self.oracle / 'sse_multivector' / source.name
        shutil.copyfile(source, copied)
        for repository in (self.oracle, self.runner):
            self.git(repository, 'add', '.')
            message = self.root / ('oracle-message' if repository == self.oracle else 'runner-message')
            message.write_text('Initialize provenance fixture\n')
            self.git(repository, 'commit', '--quiet', '-F', str(message))
        spec = importlib.util.spec_from_file_location('publication_provenance_fixture', copied)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.package = SimpleNamespace(__file__=str(self.runner / 'experiment_runner/__init__.py'))
        packages = patch.dict(sys.modules, experiment_runner=self.package)
        packages.start()
        self.addCleanup(packages.stop)

    def git(self, repository, *arguments):
        return subprocess.check_output(['git', '-C', str(repository), *arguments], text=True).strip()

    def capture(self):
        return self.module.capture({'note_ids': ['used', 'unknown', 'missing']}, [
            {'note_id': 'unused', 'origin': {'prompt_version': 'ASv1'}},
            {'note_id': 'used', 'origin': {'prompt_version': 'ASv6.100'}},
            {'note_id': 'unknown'},
        ])

    def test_selected_subject_versions_and_current_commits_are_explicit(self):
        captured = self.capture()
        self.assertEqual(captured, {
            'code': {
                'oracle': {'commit': self.git(self.oracle, 'rev-parse', 'HEAD'), 'modified': False},
                'runner': {'commit': self.git(self.runner, 'rev-parse', 'HEAD'), 'modified': False},
            },
            'subject_prompt_versions': ['ASv6.100', None],
        })
        self.assertNotIn(str(self.root), json.dumps(captured))
        self.assertNotIn('Fixture', json.dumps(captured))

    def test_only_tracked_runtime_changes_mark_the_code_modified(self):
        for repository, test in ((self.oracle, 'sse_multivector/test_example.py'),
                                 (self.runner, 'tests/test_example.py')):
            (repository / 'README.md').write_text('Changed documentation\n')
            (repository / test).write_text('# Changed test\n')
            (repository / 'ignored-corpus.json').write_text('Untracked data\n')
        self.assertFalse(self.capture()['code']['oracle']['modified'])
        self.assertFalse(self.capture()['code']['runner']['modified'])
        (self.oracle / 'sse_multivector/generation.py').write_text('value = 2\n')
        (self.runner / 'experiment_runner/experiment.py').write_text('value = 2\n')
        self.assertTrue(self.capture()['code']['oracle']['modified'])
        self.assertTrue(self.capture()['code']['runner']['modified'])

    def test_unavailable_git_history_is_recorded_as_unknown(self):
        shutil.rmtree(self.runner / '.git')
        self.assertEqual(self.capture()['code']['runner'], {'commit': None, 'modified': None})

    def test_runner_revision_comes_from_the_executing_package(self):
        relocated = self.root / 'installed-runner'
        self.runner.rename(relocated)
        self.package.__file__ = str(relocated / 'experiment_runner/__init__.py')
        self.assertEqual(self.capture()['code']['runner'], {
            'commit': self.git(relocated, 'rev-parse', 'HEAD'), 'modified': False})


if __name__ == '__main__':
    unittest.main()
