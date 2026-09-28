import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { HYDROMETRIC_MODEL_ID, HYDROMETRIC_MODEL_VERSION, validProjection, type Projection } from '../lib/projection.ts';

function fixture(): Projection {
  const referenceAt = '2026-09-23T13:00:00Z';
  return {
    schema: 1, station: 'mucum', experimental: true, intervalMinutes: 15, horizonHours: 6,
    modelVersion: HYDROMETRIC_MODEL_VERSION, modelSha256: 'a'.repeat(64),
    archiveReceiptKey: 'projection/receipts/fixture.json',
    generatedAt: '2026-09-23T15:05:00Z', referenceAt, forecastStartLeadHours: 3,
    observation: { timestamp: referenceAt, level: 12 },
    models: [{ id: HYDROMETRIC_MODEL_ID, label: 'Modelo hidrométrico', points: [3, 4, 5, 6].map(lead => ({
      timestamp: new Date(Date.parse(referenceAt) + lead * 3_600_000).toISOString(), level: 12 + lead / 10,
    })) }],
  };
}

test('modelo hidrométrico público mantém identidade, referência, recibo e sufixo futuro', () => {
  assert.ok(validProjection(fixture()));
  for (const patch of [
    { station: undefined }, { station: 'encantado' }, { modelVersion: 'mucum-hydrometry-shadow-v1' },
    { modelVersion: undefined }, { modelSha256: undefined }, { modelSha256: 'bad' },
    { archiveReceiptKey: undefined }, { archiveReceiptKey: 'projection/receipts/../private.json' },
    { generatedAt: '2026-09-23T15:05:00' }, { referenceAt: '2026-09-23T13:00:00' },
    { referenceAt: '2026-09-23T13:01:00Z' },
    { observation: { timestamp: '2026-09-23T12:00:00Z', level: 12 } },
    { generatedAt: '2026-09-23T16:01:00Z', forecastStartLeadHours: 4,
      models: [{ ...fixture().models[0], points: fixture().models[0].points.slice(1) }] },
    { models: [{ ...fixture().models[0], points: [null] }] },
    { models: [{ ...fixture().models[0], points: {} }] },
  ]) assert.equal(validProjection({ ...fixture(), ...patch }), false, JSON.stringify(patch));
  const anotherStation = { ...fixture(), station: 'encantado' };
  assert.equal(validProjection(anotherStation, 'encantado'), false);
  const expired = fixture(); expired.models[0].points[0].timestamp = expired.generatedAt;
  assert.equal(validProjection(expired), false);
});

test('publica modelo hidrométrico sem checkpoints legados, mantendo a barreira de arquivo e a referência', async context => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'projection-hydrometric-'));
  const remoteUrl = 'https://hydrometric.local.test';
  process.env.MONITORA_DATA_DIR = root;
  process.env.PROJECTION_RUNTIME_DIR = root;
  process.env.PROJECTION_PYTHON = process.execPath;
  process.env.OBJECT_STORAGE_URL = remoteUrl;
  const hash = (body: Buffer) => createHash('sha256').update(body).digest('hex');
  const objects = new Map<string, Buffer>();
  const requests: { method: string; key: string }[] = [];
  let beforePut = async (_key: string) => {};
  let failReceipts = false;
  context.mock.method(globalThis, 'fetch', async (input: string | URL | Request, init?: RequestInit) => {
    const request = new Request(input, init);
    const url = new URL(request.url);
    assert.equal(url.origin, remoteUrl, 'The test must never contact production');
    const key = decodeURIComponent(url.pathname.slice(1));
    requests.push({ method: request.method, key });
    if (request.method === 'PUT') {
      await beforePut(key);
      if (failReceipts && key.startsWith('projection/receipts/')) return new Response(null, { status: 503 });
      const bytes = Buffer.from(await request.arrayBuffer());
      if (request.headers.get('if-none-match') === '*' && objects.has(key)) return new Response(null, { status: 412 });
      objects.set(key, bytes);
      return new Response(null, { status: 201 });
    }
    const bytes = objects.get(key);
    if (!bytes) return new Response(null, { status: 404 });
    if (request.method === 'HEAD') return new Response(null, { headers: { 'x-content-sha256': hash(bytes) } });
    assert.equal(request.method, 'GET');
    return new Response(Uint8Array.from(bytes));
  });
  try {
    const referenceAt = new Date(Math.floor(Date.now() / 3_600_000) * 3_600_000).toISOString();
    const legacy = {
      ...fixture(), station: undefined, modelVersion: undefined, modelSha256: undefined, archiveReceiptKey: undefined,
      referenceAt, generatedAt: new Date(Date.parse(referenceAt) + 1).toISOString(), forecastStartLeadHours: 1,
      observation: { timestamp: referenceAt, level: 12 },
      models: [{ id: 'radar_arvores_live_candidate', label: 'Modelo anterior', points: [1, 2, 3, 4, 5, 6].map(lead => ({
        timestamp: new Date(Date.parse(referenceAt) + lead * 3_600_000).toISOString(), level: 12,
      })) }],
    };
    const legacyBytes = Buffer.from(JSON.stringify(legacy));
    objects.set('projection/latest.json', legacyBytes);
    const script = path.join(root, 'scripts/hydro_site_projection.py');
    await mkdir(path.dirname(script), { recursive: true });
    const fake = ({ mismatch = false, waiting = false, offset = 0 } = {}) => `
      const fs=require('node:fs'), crypto=require('node:crypto'), args=process.argv;
      if(args.includes('--after-reference')) throw new Error('A legacy issue must not block same-hour model migration');
      const state=args[args.indexOf('--state')+1], attemptId=args[args.indexOf('--attempt-id')+1], checkedReferenceAt=args[args.indexOf('--reference')+1];
      const referenceAt=new Date(Date.parse(checkedReferenceAt)+${offset}*3600000).toISOString(), generatedAt=new Date().toISOString();
      const archiveReceiptKey='projection/receipts/'+attemptId+'.json', status=${JSON.stringify(waiting ? 'waiting_for_data' : 'calculated')};
      fs.mkdirSync(state+'/archive/blobs',{recursive:true}); fs.mkdirSync(state+'/archive/pending',{recursive:true});
      const objects=['runtime','attempt'].map(role=>{
        const body=Buffer.from(role+'-'+attemptId),sha256=crypto.createHash('sha256').update(body).digest('hex');
        fs.writeFileSync(state+'/archive/blobs/'+sha256+'.tar.gz',body);
        return {key:'projection/blobs/'+sha256+'.tar.gz',sha256,bytes:body.length,role};
      });
      fs.writeFileSync(state+'/archive/pending/'+attemptId+'.json',JSON.stringify({schema:'radar-archive-receipt/v1',attemptId,referenceAt,status,generatedAt,objects}));
      fs.writeFileSync(state+'/refresh-status.json',JSON.stringify({attemptId,referenceAt,checkedReferenceAt,status,generatedAt,archiveReceiptKey,missing:['fixture missing hydrometric observation']}));
      const first=Math.floor((Date.parse(generatedAt)-Date.parse(referenceAt))/3600000)+1;
      fs.writeFileSync(state+'/result.json',JSON.stringify({schema:1,station:'mucum',experimental:true,intervalMinutes:15,horizonHours:6,
        referenceAt,generatedAt,forecastStartLeadHours:first,modelVersion:'${HYDROMETRIC_MODEL_VERSION}',modelSha256:'${'a'.repeat(64)}',
        archiveReceiptKey:${mismatch ? "'projection/receipts/wrong-attempt.json'" : 'archiveReceiptKey'},
        observation:{timestamp:referenceAt,level:12},models:[{id:'${HYDROMETRIC_MODEL_ID}',label:'Modelo hidrométrico',
          points:Array.from({length:7-first},(_,i)=>({timestamp:new Date(Date.parse(referenceAt)+(i+first)*3600000).toISOString(),level:12+i}))}]}));
    `;
    await writeFile(script, fake());
    let started!: () => void;
    let resume!: () => void;
    const reachedBlob = new Promise<void>(resolve => { started = resolve; });
    const gate = new Promise<void>(resolve => { resume = resolve; });
    let first = true;
    beforePut = async key => { if (first && key.startsWith('projection/blobs/')) { first = false; started(); await gate; } };
    const { refreshProjection } = await import('../lib/projection-server.ts');
    const refreshing = refreshProjection();
    await reachedBlob;
    assert.deepEqual(objects.get('projection/latest.json'), legacyBytes);
    assert.ok(!requests.some(r => r.method === 'PUT' && (r.key.includes('/receipts/') || r.key.includes('/issues/') || r.key.endsWith('/latest.json'))));
    resume();
    const published = await refreshing;
    assert.equal(published.status, 'published');
    assert.equal(published.referenceAt, referenceAt, 'The model can replace the legacy issue at the same original hour');
    assert.equal(published.missing, undefined);
    const latest = JSON.parse(objects.get('projection/latest.json')!.toString());
    assert.equal(latest.models[0].id, HYDROMETRIC_MODEL_ID);
    assert.equal(latest.modelVersion, HYDROMETRIC_MODEL_VERSION);
    assert.equal(latest.missing, undefined);
    assert.ok(objects.has(latest.archiveReceiptKey));
    assert.ok(objects.has('projection/issues/' + latest.generatedAt + '.json'));
    assert.ok(!requests.some(r => r.key.endsWith('/history.tar.gz') || r.key.endsWith('/audit.tar.gz')));
    await assert.rejects(readFile(path.join(root, 'projection/history.tar.gz')), /ENOENT/);
    const uploads = requests.filter(r => r.method === 'PUT').map(r => r.key);
    assert.ok(uploads[2].startsWith('projection/receipts/'));
    assert.equal(uploads.at(-2), 'projection/latest.json');
    process.env.PROJECTION_PYTHON = '/must-not-recalculate-hydrometric-hour';
    assert.equal((await refreshProjection()).status, 'already_calculated');
    process.env.PROJECTION_PYTHON = process.execPath;
    beforePut = async () => {};

    // Missing intrinsic observations, a receipt outage, a mismatched receipt and
    // an older origin must each leave the already stored public document alone.
    for (const scenario of ['waiting', 'archive', 'mismatch', 'older']) {
      objects.set('projection/latest.json', legacyBytes);
      await writeFile(script, fake({ waiting: scenario === 'waiting', mismatch: scenario === 'mismatch', offset: scenario === 'older' ? -1 : 0 }));
      failReceipts = scenario === 'archive';
      const start = requests.length;
      if (scenario === 'waiting') assert.equal((await refreshProjection()).status, 'waiting_for_data');
      else await assert.rejects(refreshProjection(), scenario === 'archive' ? /503/ : scenario === 'mismatch' ? /receipt does not match/ : /Invalid selected reference/);
      assert.deepEqual(objects.get('projection/latest.json'), legacyBytes, scenario);
      assert.ok(!requests.slice(start).some(r => r.method === 'PUT' && r.key === 'projection/latest.json'), scenario);
      failReceipts = false;
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
