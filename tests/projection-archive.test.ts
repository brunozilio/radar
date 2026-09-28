import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import test, { after, type TestContext } from 'node:test';
import vm from 'node:vm';
import { isProjectionObjectKey, isImmutableProjectionObjectKey } from '../cloudflare/projection-storage.js';

// Every fetch in this file is intercepted; no Cloudflare/provider is contacted.
const root = await mkdtemp(path.join(os.tmpdir(), 'projection-archive-'));
const remoteUrl = 'https://archive.local.test';
process.env.OBJECT_STORAGE_URL = remoteUrl;
process.env.MONITORA_DATA_DIR = root;
process.env.PROJECTION_RUNTIME_DIR = root;
process.env.PROJECTION_PYTHON = process.execPath;
const { flushProjectionArchive, requireArchivedReceipt } = await import('../lib/projection-archive.ts');
const { putImmutableStoredObject } = await import('../lib/object-storage.ts');
after(async () => { await rm(root, { recursive: true, force: true }); });
const hash = (body: Buffer) => createHash('sha256').update(body).digest('hex');
const referenceAt = new Date(Math.floor(Date.now() / 3_600_000) * 3_600_000).toISOString();

function remote(context: TestContext) {
  const state = {
    objects: new Map<string, { bytes: Buffer; sha256: string }>(),
    requests: [] as Array<{ method: string; key: string }>,
    failKey: '',
    beforePut: async (_key: string) => {},
  };
  context.mock.method(globalThis, 'fetch', async (input: string | URL | Request, init?: RequestInit) => {
    const request = new Request(input, init);
    const url = new URL(request.url);
    assert.equal(url.origin, remoteUrl, 'A test must not contact another host');
    const key = decodeURIComponent(url.pathname.slice(1));
    state.requests.push({ method: request.method, key });
    if (request.method === 'PUT') {
      await state.beforePut(key);
      if (key === state.failKey) return new Response('fixture outage', { status: 503 });
      const bytes = Buffer.from(await request.arrayBuffer());
      const metadata = JSON.parse(Buffer.from(request.headers.get('x-monitora-metadata')!, 'base64url').toString());
      if (isImmutableProjectionObjectKey(key)) {
        assert.equal(request.headers.get('if-none-match'), '*');
        assert.equal(metadata.sha256, hash(bytes));
        if (state.objects.has(key)) return new Response(null, { status: 412 });
      }
      state.objects.set(key, { bytes, sha256: hash(bytes) });
      return new Response(null, { status: 201 });
    }
    const previous = state.objects.get(key);
    if (!previous) return new Response(null, { status: 404 });
    if (request.method === 'HEAD') return new Response(null, { headers: { 'x-content-sha256': previous.sha256 } });
    assert.equal(request.method, 'GET');
    return new Response(Uint8Array.from(previous.bytes));
  });
  return state;
}

async function enqueue(directory: string, attemptId: string) {
  const objects = ['runtime', 'attempt'].map(role => {
    const bytes = Buffer.from(role === 'runtime' ? 'shared-runtime' : `${role}-${attemptId}`);
    const sha256 = hash(bytes);
    return { key: `projection/blobs/${sha256}.tar.gz`, sha256, bytes: bytes.length, role, body: bytes };
  });
  await mkdir(path.join(directory, 'archive/blobs'), { recursive: true });
  await mkdir(path.join(directory, 'archive/pending'), { recursive: true });
  for (const object of objects) await writeFile(path.join(directory, 'archive/blobs', `${object.sha256}.tar.gz`), object.body);
  const receipt = {
    schema: 'radar-archive-receipt/v1', attemptId, referenceAt, status: 'waiting_for_data', generatedAt: null,
    objects: objects.map(({ body: _body, ...object }) => object), missing: ['fixture missing rain'],
  };
  const receiptPath = path.join(directory, 'archive/pending', `${attemptId}.json`);
  await writeFile(receiptPath, JSON.stringify(receipt));
  return { receipt, receiptPath, objects };
}

test('blobs são confirmados antes do recibo; falha mantém a fila e retry é idempotente', async context => {
  const store = remote(context);
  const directory = path.join(root, 'retry');
  const fixture = await enqueue(directory, 'retry-1');
  store.failKey = fixture.objects[1].key;
  await assert.rejects(flushProjectionArchive(directory), /503/);
  assert.ok(await readFile(fixture.receiptPath));
  assert.equal(store.objects.size, 1);
  assert.ok(!store.requests.some(({ key }) => key.startsWith('projection/receipts/')));
  store.failKey = '';
  await flushProjectionArchive(directory);
  assert.ok(store.requests.some(({ method, key }) => method === 'HEAD' && key === fixture.objects[0].key));
  assert.equal(store.objects.size, 3);
  assert.equal(store.requests.at(-1)?.key, 'projection/receipts/retry-1.json');
  await assert.rejects(readFile(fixture.receiptPath), /ENOENT/);
  assert.ok(await readFile(path.join(directory, 'archive/receipts/retry-1.json')));
  assert.deepEqual(await readdir(path.join(directory, 'archive/blobs')), []);
  const count = store.requests.length;
  await flushProjectionArchive(directory);
  assert.equal(store.requests.length, count);
});

test('recibo recusado mantém os blobs locais; retomada confirma hashes sem reescrever evidência', async context => {
  const store = remote(context);
  const directory = path.join(root, 'receipt-failure');
  const fixture = await enqueue(directory, 'receipt-failure');
  store.failKey = 'projection/receipts/receipt-failure.json';
  await assert.rejects(flushProjectionArchive(directory), /503/);
  assert.ok(await readFile(fixture.receiptPath));
  assert.equal((await readdir(path.join(directory, 'archive/blobs'))).length, 2);
  store.failKey = '';
  const retriedAt = store.requests.length;
  await flushProjectionArchive(directory);
  assert.equal(store.requests.slice(retriedAt).filter(({ method }) => method === 'HEAD').length, 3);
  assert.equal(store.requests.slice(retriedAt).filter(({ method, key }) => method === 'PUT' && key.startsWith('projection/blobs/')).length, 0);
  assert.equal(store.objects.size, 3);
});

test('retry confirma SHA-256 por HEAD sem reenviar um objeto idêntico', async context => {
  const store = remote(context);
  const bytes = Buffer.from('same-body');
  const key = 'projection/receipts/collision.json';
  const input = { key, bytes, mimeType: 'application/json', localPath: path.join(root, 'not-written') };
  await putImmutableStoredObject(input);
  await putImmutableStoredObject(input);
  assert.deepEqual(store.requests.map(({ method }) => method), ['HEAD', 'PUT', 'HEAD']);
  await assert.rejects(putImmutableStoredObject({ ...input, bytes: Buffer.from('different-body') }), /Immutable object conflict/);
  assert.deepEqual(store.objects.get(key)?.bytes, bytes);
});

test('criação concorrente entre HEAD e PUT só é aceita com o mesmo SHA-256', async context => {
  const store = remote(context);
  const bytes = Buffer.from('same-concurrent-body');
  const input = { key: 'projection/receipts/race.json', bytes, mimeType: 'application/json', localPath: path.join(root, 'race-not-written') };
  store.beforePut = async key => { store.objects.set(key, { bytes, sha256: hash(bytes) }); };
  await putImmutableStoredObject(input);
  assert.deepEqual(store.requests.map(({ method }) => method), ['HEAD', 'PUT', 'HEAD']);
  const conflicting = Buffer.from('conflicting-concurrent-body');
  store.beforePut = async key => { store.objects.set(key, { bytes: conflicting, sha256: hash(conflicting) }); };
  await assert.rejects(putImmutableStoredObject({ ...input, key: 'projection/receipts/conflicting-race.json' }), /Immutable object conflict/);
  assert.deepEqual(store.objects.get('projection/receipts/conflicting-race.json')?.bytes, conflicting);
});

test('HEAD indisponível preserva a falha de armazenamento e não tenta sobrescrever', async context => {
  context.mock.method(globalThis, 'fetch', async (input: string | URL | Request, init?: RequestInit) => {
    const request = new Request(input, init);
    assert.equal(new URL(request.url).origin, remoteUrl);
    assert.equal(request.method, 'HEAD');
    return new Response('fixture HEAD outage', { status: 503 });
  });
  await assert.rejects(putImmutableStoredObject({ key: 'projection/receipts/head-outage.json', bytes: Buffer.from('fixture'), mimeType: 'application/json', localPath: path.join(root, 'head-not-written') }), /R2 immutable HEAD.*HTTP 503/);
});

test('duas tentativas completas compartilham runtime e arquivam ambos os recibos após limpeza local', async context => {
  const store = remote(context);
  const directory = path.join(root, 'consecutive-attempts');
  const first = await enqueue(directory, 'consecutive-1');
  await flushProjectionArchive(directory);
  assert.deepEqual(await readdir(path.join(directory, 'archive/blobs')), []);
  const second = await enqueue(directory, 'consecutive-2');
  assert.equal(first.objects[0].key, second.objects[0].key);
  await flushProjectionArchive(directory);
  assert.deepEqual(await readdir(path.join(directory, 'archive/pending')), []);
  assert.deepEqual(await readdir(path.join(directory, 'archive/receipts')), ['consecutive-1.json', 'consecutive-2.json']);
  assert.equal(store.objects.size, 5);
  assert.equal(store.requests.filter(({ method, key }) => method === 'PUT' && key === first.objects[0].key).length, 1);
});

test('resposta de PUT perdida retoma pelo checksum sem reenvio nem perda da fila', async context => {
  const store = remote(context);
  const bytes = Buffer.from('stored-before-connection-dropped');
  const input = { key: 'projection/receipts/lost-response.json', bytes, mimeType: 'application/json', localPath: path.join(root, 'lost-response-not-written') };
  store.beforePut = async key => {
    store.objects.set(key, { bytes, sha256: hash(bytes) });
    throw new Error('fixture connection dropped after storage');
  };
  await assert.rejects(putImmutableStoredObject(input), /connection dropped/);
  await putImmutableStoredObject(input);
  assert.deepEqual(store.requests.map(({ method }) => method), ['HEAD', 'PUT', 'HEAD']);
  assert.deepEqual(store.objects.get(input.key)?.bytes, bytes);
});

test('hash, tamanho, schema e caminhos inválidos impedem publicar um recibo', async context => {
  const store = remote(context);
  for (const scenario of ['corrupt', 'size', 'key', 'schema', 'attempt']) {
    const directory = path.join(root, scenario);
    const fixture = await enqueue(directory, scenario);
    if (scenario === 'corrupt') await writeFile(path.join(directory, 'archive/blobs', `${fixture.objects[0].sha256}.tar.gz`), 'damaged');
    if (scenario === 'size') fixture.receipt.objects[0].bytes++;
    if (scenario === 'key') fixture.receipt.objects[0].key = 'projection/blobs/../../private.tar.gz';
    if (scenario === 'schema') fixture.receipt.schema = 'wrong';
    if (scenario === 'attempt') fixture.receipt.attemptId = 'another-attempt';
    await writeFile(fixture.receiptPath, JSON.stringify(fixture.receipt));
    const count = store.requests.length;
    await assert.rejects(flushProjectionArchive(directory), /Archive integrity failure|Invalid archive/);
    assert.equal(store.requests.length, count);
    assert.ok(await readFile(fixture.receiptPath));
  }
});

test('arquivo local imutável aceita somente repetição idêntica', async () => {
  delete process.env.OBJECT_STORAGE_URL;
  // An isolated import exercises the local implementation without changing the remote module used by other tests.
  const local = await import(new URL('../lib/object-storage.ts?archive-local-test', import.meta.url).href);
  process.env.OBJECT_STORAGE_URL = remoteUrl;
  const localPath = path.join(root, 'local/receipt.json');
  const value = { key: 'projection/receipts/local.json', bytes: Buffer.from('original'), mimeType: 'application/json', localPath };
  await local.putImmutableStoredObject(value);
  await local.putImmutableStoredObject(value);
  await assert.rejects(local.putImmutableStoredObject({ ...value, bytes: Buffer.from('changed') }), /Immutable object conflict/);
  assert.equal(await readFile(localPath, 'utf8'), 'original');
});

test('recibo deve corresponder à rodada; somente retry da mesma emissão pode reaproveitar tentativa anterior', async () => {
  const directory = path.join(root, 'receipt-binding');
  const fixture = await enqueue(directory, 'waiting-original');
  await mkdir(path.join(directory, 'archive/receipts'), { recursive: true });
  const saved = path.join(directory, 'archive/receipts/waiting-original.json');
  const key = 'projection/receipts/waiting-original.json';
  await writeFile(saved, JSON.stringify(fixture.receipt));
  const expected = { attemptId: 'waiting-original', referenceAt, status: 'waiting_for_data' };
  await requireArchivedReceipt(directory, key, expected);
  await assert.rejects(requireArchivedReceipt(directory, key, { ...expected, attemptId: 'another-attempt' }), /does not match/);
  await assert.rejects(requireArchivedReceipt(directory, key, { ...expected, referenceAt: '2020-01-01T00:00:00Z' }), /does not match/);
  await assert.rejects(requireArchivedReceipt(directory, key, { ...expected, status: 'calculated' }), /does not match/);
  await assert.rejects(requireArchivedReceipt(directory, 'projection/receipts/../../private.json', expected), /Missing immutable/);
  await writeFile(saved, '{corrupt-json');
  await assert.rejects(requireArchivedReceipt(directory, key, expected), SyntaxError);
  await writeFile(saved, JSON.stringify({ ...fixture.receipt, schema: 'invalid' }));
  await assert.rejects(requireArchivedReceipt(directory, key, expected), /does not match/);
  const generatedAt = new Date().toISOString();
  await writeFile(saved, JSON.stringify({ ...fixture.receipt, status: 'calculated', generatedAt }));
  const retried = { attemptId: 'retry-new-process', referenceAt, status: 'calculated', generatedAt };
  await requireArchivedReceipt(directory, key, retried);
  await assert.rejects(requireArchivedReceipt(directory, key, { ...retried, generatedAt: '2020-01-01T00:00:00Z' }), /does not match/);
});

test('ponte exige criação condicional, verifica checksum R2 e proíbe excluir evidência', async () => {
  const source = await readFile(new URL('../cloudflare/index.js', import.meta.url), 'utf8');
  const start = source.indexOf('function decodeObjectMetadata(');
  const end = source.indexOf('async function handleContainerDatabase(', start);
  const handle = vm.runInNewContext(`${source.slice(start, end)}\nhandleContainerObjectStorage`, {
    __name() {}, URL, Request, Response, Headers, atob, TextDecoder,
    OBJECT_KEY_PATTERN: /^never-allow-test-non-projection$/,
    isProjectionObjectKey, isImmutableProjectionObjectKey,
    json: (value: unknown, status = 200) => Response.json(value, { status }),
  }) as (request: Request, env: unknown) => Promise<Response>;
  const body = Buffer.from('immutable fixture');
  const sha256 = hash(body);
  const key = `projection/blobs/${sha256}.tar.gz`;
  let stored = false;
  let putCount = 0;
  const env = { MEDIA_BUCKET: {
    put: async (_key: string, _body: unknown, options: { onlyIf: Headers; sha256: string; customMetadata: { sha256: string } }) => {
      putCount++;
      assert.equal(options.onlyIf.get('If-None-Match'), '*');
      assert.equal(options.sha256, sha256);
      assert.equal(options.customMetadata.sha256, sha256);
      if (stored) return null;
      stored = true;
      return { key };
    },
    head: async () => ({ httpEtag: 'fixture-etag', customMetadata: { sha256 } }),
    delete: async () => assert.fail('Immutable evidence must never be deleted'),
  } };
  const headers = { 'if-none-match': '*', 'x-monitora-metadata': Buffer.from(JSON.stringify({ sha256 })).toString('base64url') };
  const request = (method: string, requestKey = key, requestHeaders = headers) => new Request(`${remoteUrl}/${requestKey}`, {
    method, headers: requestHeaders, ...(method === 'PUT' ? { body: Uint8Array.from(body) } : {}),
  });
  assert.equal((await handle(request('PUT', key, { ...headers, 'if-none-match': '' }), env)).status, 400);
  assert.equal((await handle(request('PUT', key, { ...headers, 'x-monitora-metadata': Buffer.from('{}').toString('base64url') }), env)).status, 400);
  assert.equal((await handle(request('PUT', `projection/blobs/${'0'.repeat(64)}.tar.gz`), env)).status, 400);
  assert.equal(putCount, 0);
  assert.equal((await handle(request('PUT'), env)).status, 201);
  assert.equal((await handle(request('PUT'), env)).status, 412);
  assert.equal((await handle(request('HEAD'), env)).headers.get('x-content-sha256'), sha256);
  for (const immutable of [key, 'projection/receipts/attempt-1.json', 'projection/issues/2026-09-22T20:00:00.000Z.json']) {
    assert.equal((await handle(request('DELETE', immutable), env)).status, 405);
  }
  for (const invalid of ['projection/blobs/../private.json', 'projection/receipts/%2fprivate.json', 'projection/blobs/not-a-hash.tar.gz']) {
    assert.equal((await handle(request('PUT', invalid), env)).status, 400);
  }
});

test('refresh espera o arquivo completo e publica latest somente após blobs e recibo', async context => {
  const store = remote(context);
  const script = path.join(root, 'scripts/hydro_site_projection.py');
  await mkdir(path.dirname(script), { recursive: true });
  await writeFile(script, `
    const fs=require('node:fs'),crypto=require('node:crypto'),args=process.argv;
    const state=args[args.indexOf('--state')+1],attemptId=args[args.indexOf('--attempt-id')+1],referenceAt=args[args.indexOf('--reference')+1];
    const generatedAt=new Date().toISOString();
    fs.mkdirSync(state+'/archive/blobs',{recursive:true}); fs.mkdirSync(state+'/archive/pending',{recursive:true});
    const objects=['runtime','attempt'].map(role=>{const bytes=Buffer.from(role+'-'+attemptId),sha256=crypto.createHash('sha256').update(bytes).digest('hex'); fs.writeFileSync(state+'/archive/blobs/'+sha256+'.tar.gz',bytes); return {key:'projection/blobs/'+sha256+'.tar.gz',sha256,bytes:bytes.length,role};});
    fs.writeFileSync(state+'/archive/pending/'+attemptId+'.json',JSON.stringify({schema:'radar-archive-receipt/v1',attemptId,referenceAt,status:'calculated',generatedAt,objects}));
    fs.writeFileSync(state+'/refresh-status.json',JSON.stringify({attemptId,referenceAt,checkedReferenceAt:referenceAt,status:'calculated',generatedAt,archiveReceiptKey:'projection/receipts/'+attemptId+'.json',
      shadow:{status:'calculated',generatedAt,referenceAt,archiveReceiptKey:'projection/receipts/'+attemptId+'.json',modelVersion:'mucum-hydrometry-shadow-v1',points:[{level:99}]}}));
    fs.writeFileSync(state+'/result.json',JSON.stringify({schema:1,experimental:true,intervalMinutes:15,horizonHours:6,referenceAt,generatedAt,observation:{timestamp:referenceAt,level:12},models:[{id:'radar_arvores_live_candidate',label:'Modelo de previsão',points:Array.from({length:6},(_,i)=>({timestamp:new Date(Date.parse(referenceAt)+(i+1)*3600000).toISOString(),level:12+i}))}]}));
    fs.writeFileSync(state+'/history.tar.gz','history');fs.writeFileSync(state+'/audit.tar.gz','audit');
  `);
  let started!: () => void;
  let resume!: () => void;
  const reachedBlob = new Promise<void>(resolve => { started = resolve; });
  const gate = new Promise<void>(resolve => { resume = resolve; });
  let first = true;
  store.beforePut = async key => { if (first && key.startsWith('projection/blobs/')) { first = false; started(); await gate; } };
  const { refreshProjection } = await import('../lib/projection-server.ts');
  const refreshing = refreshProjection();
  await reachedBlob;
  assert.equal(store.objects.size, 0);
  assert.ok(!store.requests.some(({ method, key }) => method === 'PUT' && (key.includes('/receipts/') || key.endsWith('/latest.json') || key.endsWith('/refresh.json'))));
  resume();
  const result = await refreshing;
  assert.equal(result.status, 'published');
  assert.equal(result.shadow?.status, 'calculated');
  assert.equal(Object.hasOwn(result.shadow!, 'points'), false);
  const uploads = store.requests.filter(({ method }) => method === 'PUT').map(({ key }) => key);
  assert.ok(uploads[0].startsWith('projection/blobs/'));
  assert.ok(uploads[1].startsWith('projection/blobs/'));
  assert.ok(uploads[2].startsWith('projection/receipts/'));
  assert.equal(uploads.at(-2), 'projection/latest.json');
  assert.equal(uploads.at(-1), 'projection/refresh.json');
  assert.deepEqual(JSON.parse(store.objects.get('projection/refresh.json')!.bytes.toString()).shadow, result.shadow);
  const latest = JSON.parse(store.objects.get('projection/latest.json')!.bytes.toString());
  assert.equal(latest.referenceAt, result.referenceAt);
});

test('alvo que vence durante upload preserva evidência e não vira latest', async context => {
  const store = remote(context);
  const clock = context.mock.method(Date, 'now', () => new Date().getTime());
  store.beforePut = async key => {
    if (key === 'projection/history.tar.gz') {
      clock.mock.mockImplementation(() => Date.parse(referenceAt) + 3_600_001);
    }
  };
  const { refreshProjection } = await import('../lib/projection-server.ts');
  await assert.rejects(refreshProjection(), /Forecast target elapsed during upload/);
  assert.ok([...store.objects.keys()].some(key => key.startsWith('projection/receipts/')));
  assert.ok(!store.requests.some(({ method, key }) => method === 'PUT' && key === 'projection/latest.json'));
});
