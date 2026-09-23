// Local workerd/R2 simulation of the actual private bridge. No remote bindings.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { Miniflare, convertV4MiniflareOptions } from 'miniflare';

const source = await readFile('cloudflare/index.js', 'utf8');
const start = source.indexOf('function decodeObjectMetadata(');
const end = source.indexOf('async function handleContainerDatabase(', start);
assert.ok(start >= 0 && end > start);
const rules = await readFile('cloudflare/projection-storage.js', 'utf8');
const script = `const __name=()=>{};
const OBJECT_KEY_PATTERN=/^never-allow-test$/;
const json=(value,status=200)=>Response.json(value,{status});
${rules}
${source.slice(start, end)}
export default {fetch:handleContainerObjectStorage};`;
const mf = new Miniflare({
  ...convertV4MiniflareOptions({script, modules:true, compatibilityDate:'2026-09-01', r2Buckets:['MEDIA_BUCKET'], cf:false}),
  telemetry:{enabled:false},
});
try {
  const bytes = Buffer.from('real-r2-binding-check');
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  const url = `http://local/projection/blobs/${sha256}.tar.gz`;
  const results = [];
  for (let i = 0; i < 2; i++) {
    const response = await mf.dispatchFetch(url, {method:'PUT', headers:{
      'content-length':String(bytes.length), 'if-none-match':'*',
      'x-monitora-metadata':Buffer.from(JSON.stringify({sha256})).toString('base64url'),
    }, body:bytes});
    results.push({attempt:i+1, status:response.status, body:await response.json()});
  }
  assert.equal(results[0].status, 201);
  assert.equal(results[1].status, 412);
  const head = await mf.dispatchFetch(url, {method:'HEAD'});
  assert.equal(head.status, 200);
  assert.equal(head.headers.get('x-content-sha256'), sha256);
  const get = await mf.dispatchFetch(url);
  assert.deepEqual(Buffer.from(await get.arrayBuffer()), bytes);
  // Exercise the actual Node client through HTTP with the production-sized
  // runtime body, rather than replacing fetch with an in-memory mock.
  const origin = (await mf.ready).origin;
  process.env.OBJECT_STORAGE_URL = origin;
  const { putImmutableStoredObject } = await import('../../lib/object-storage.ts');
  const large = Buffer.alloc(8_831_591, 0x5a);
  const largeSha = createHash('sha256').update(large).digest('hex');
  const input = {key:`projection/blobs/${largeSha}.tar.gz`, bytes:large,
    mimeType:'application/gzip', localPath:'/unused-local-test-path'};
  const nativeFetch = globalThis.fetch;
  const largeRequests = [];
  globalThis.fetch = async (url, init) => {
    assert.equal(new URL(url).origin, origin);
    const response = await nativeFetch(url, init);
    largeRequests.push({method:init?.method || 'GET', status:response.status,
      bytesSent:init?.body?.byteLength || 0});
    return response;
  };
  try {
    await putImmutableStoredObject(input);
    await putImmutableStoredObject(input);
    assert.deepEqual(largeRequests.map(row => [row.method,row.status]), [['HEAD',404],['PUT',201],['HEAD',200]]);
  } finally { globalThis.fetch = nativeFetch; }
  const duplicateLarge = await nativeFetch(`${origin}/${input.key}`, {method:'PUT',
    headers:{'if-none-match':'*','x-monitora-metadata':Buffer.from(JSON.stringify({sha256:largeSha})).toString('base64url')},
    body:large});
  assert.equal(duplicateLarge.status, 412);
  await duplicateLarge.arrayBuffer();
  const report = {mode:'local workerd/Miniflare with isolated R2 binding', remoteRequests:false,
    checkedAt:new Date().toISOString(), results, head:{status:head.status, sha256},
    largeRuntime:{bytes:large.length, requests:largeRequests, rawDuplicateStatus:duplicateLarge.status},
    conclusion:'Local conditional duplicates (small and 8.8 MB) return 412. The patched real client uploads the large body once and validates repeats by HEAD only. Production ContainerProxy streaming behavior is not simulated.'};
  await writeFile(new URL('./r2-binding-smoke.json', import.meta.url), JSON.stringify(report, null, 2)+'\n');
  console.log(JSON.stringify(report));
} finally { await mf.dispose(); }
