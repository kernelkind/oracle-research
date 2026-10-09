"""Locate the shared package; project worktrees do not own runner implementations."""
import importlib
import os
from pathlib import Path
import sys


def shared(module):
    explicit = os.environ.get('EXPERIMENT_RUNNER_ROOT')
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root / 'experiment_runner/__init__.py').is_file():
            raise ImportError('EXPERIMENT_RUNNER_ROOT must name an experiment-runner checkout')
        sys.path.insert(0, str(root))
    try:
        import experiment_runner
    except ModuleNotFoundError as error:
        if error.name != 'experiment_runner':
            raise
        root = Path(__file__).resolve().parents[2] / 'experiment-runner'
        if not (root / 'experiment_runner/__init__.py').is_file():
            raise ImportError('Install experiment-runner or set EXPERIMENT_RUNNER_ROOT') from error
        sys.path.insert(0, str(root))
        import experiment_runner
    if explicit and not Path(experiment_runner.__file__).resolve().is_relative_to(root):
        raise ImportError('a different experiment-runner version is already loaded')
    from experiment_runner import project
    project.configure(Path(__file__).resolve().parents[1])
    return importlib.import_module('experiment_runner.' + module)
