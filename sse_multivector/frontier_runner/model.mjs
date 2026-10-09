import { shared } from './_shared.mjs';
import { pathToFileURL } from 'node:url';
const implementation = await import(shared('model.mjs'));
export const { VERSION, prepare, execute, preview, launchWithSelectedPi, localPiConnection, main } = implementation;
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
}
