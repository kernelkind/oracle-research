import { shared } from './_shared.mjs';
const implementation = await import(shared('websocket.mjs'));
export const { websocketRequest, websocketResponse } = implementation;
