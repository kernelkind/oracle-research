import { shared } from './_shared.mjs';
const implementation = await import(shared('backoff.mjs'));
export const { experimentAdmission } = implementation;
