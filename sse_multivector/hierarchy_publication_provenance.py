"""Small preparation-time version records without local paths or Git identity."""
from pathlib import Path
import os
import re
import subprocess
import sys


_ORACLE_RUNTIME = (
    ':(glob)sse_multivector/**/*.py',
    ':(glob)sse_multivector/**/*.sh',
    ':(glob)src/**/*.rs', 'Cargo.toml', 'Cargo.lock',
)
_RUNNER_RUNTIME = (
    ':(glob)experiment_runner/**/*.py',
    ':(glob)experiment_runner/**/*.sh',
    ':(glob)experiment_runner/**/*.js',
    ':(glob)experiment_runner/**/*.mjs',
    ':(glob)experiment_runner/**/*.json',
    'bin/experiment-runner', 'pyproject.toml',
)
_EXCLUDE_TESTS = (
    ':(exclude,glob)**/test_*.py',
    ':(exclude,glob)**/*.test.mjs',
    ':(exclude,glob)**/*.test.js',
)


def _code(repository, paths):
    unknown = dict(commit=None, modified=None)
    command = ['git', '--no-optional-locks', '-C', str(repository)]
    try:
        revision = subprocess.run(
            [*command, 'rev-parse', '--show-toplevel', 'HEAD'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10,
        )
        lines = revision.stdout.splitlines()
        if (revision.returncode or len(lines) != 2
                or Path(lines[0]).resolve() != repository.resolve()
                or not re.fullmatch('[0-9a-f]{40,64}', lines[1])):
            return unknown
        changed = subprocess.run(
            [*command, 'status', '--porcelain=v1', '--untracked-files=no',
             '--ignore-submodules=all', '--', *paths, *_EXCLUDE_TESTS],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10,
        )
        return dict(commit=lines[1],
                    modified=bool(changed.stdout) if changed.returncode == 0 else None)
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return unknown


def capture(state, corpus_notes):
    """Capture selected subjects and current source checkouts while preparing.

    Source hashes frozen in the state remain the exact code/input bindings.
    Commit and modified status describe these checkouts, including dirty runs;
    they do not assert that a commit alone reproduces their saved source bytes.
    """
    remaining = set(state['note_ids'])
    versions = set()
    for note in corpus_notes:
        if note['note_id'] not in remaining:
            continue
        remaining.remove(note['note_id'])
        origin = note.get('origin')
        version = origin.get('prompt_version') if isinstance(origin, dict) else None
        versions.add(version if isinstance(version, str) and version.strip() else None)
    if remaining:
        versions.add(None)
    oracle = Path(__file__).resolve().parents[1]
    package_file = getattr(sys.modules.get('experiment_runner'), '__file__', None)
    if package_file is not None:
        runner = Path(package_file).resolve().parents[1]
    elif os.environ.get('EXPERIMENT_RUNNER_ROOT'):
        runner = Path(os.environ['EXPERIMENT_RUNNER_ROOT']).expanduser().resolve()
    else:
        nested = oracle / 'experiment-runner'
        runner = nested if nested.exists() else oracle.parent / 'experiment-runner'
    return dict(
        code=dict(oracle=_code(oracle, _ORACLE_RUNTIME),
                  runner=_code(runner, _RUNNER_RUNTIME)),
        subject_prompt_versions=[*sorted(v for v in versions if v is not None),
                                 *([None] if None in versions else [])],
    )
