import { fileURLToPath, pathToFileURL } from 'node:url';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
export function shared(name) {
  const root = process.env.EXPERIMENT_RUNNER_ROOT
    || ['../../experiment-runner/', '../../../experiment-runner/']
      .map(relative => fileURLToPath(new URL(relative, import.meta.url)))
      .find(candidate => existsSync(join(candidate, 'experiment_runner/frontier_runner/model.mjs')));
  if (!root) throw new Error('Initialize experiment-runner or set EXPERIMENT_RUNNER_ROOT to its checkout.');
  return pathToFileURL(join(root, 'experiment_runner/frontier_runner', name)).href;
}
