#!/usr/bin/env python3
"""Compatibility entry point for the shared experiment-runner package."""
import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _runner_bootstrap import shared
else:
    from ._runner_bootstrap import shared

implementation = shared('experiment')
if __name__ == '__main__':
    raise SystemExit(implementation.main())
else:
    globals().update({k: v for k, v in vars(implementation).items() if k not in {
        '__name__', '__loader__', '__package__', '__spec__', '__file__', '__cached__'}})
    sys.modules[__name__] = implementation
