import { fileURLToPath, pathToFileURL } from 'node:url';
import { join } from 'node:path';
export function shared(name) {
  const root = process.env.EXPERIMENT_RUNNER_ROOT
    || fileURLToPath(new URL('../../../experiment-runner/', import.meta.url));
  return pathToFileURL(join(root, 'experiment_runner/frontier_runner', name)).href;
}
