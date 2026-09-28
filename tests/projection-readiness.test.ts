import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

test('aguarda dados sem publicar, rejeita resultado de outra tentativa e não recalcula a mesma hora', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'projection-readiness-'));
  process.env.MONITORA_DATA_DIR = root;
  process.env.PROJECTION_RUNTIME_DIR = root;
  process.env.PROJECTION_PYTHON = process.execPath;
  delete process.env.OBJECT_STORAGE_URL;
  try {
    const dir = path.join(root, 'projection');
    const script = path.join(root, 'scripts/hydro_site_projection.py');
    await mkdir(path.dirname(script), { recursive: true });
    await mkdir(dir);
    const current = Math.floor(Date.now() / 3600000) * 3600000;
    const fixture = (reference: number) => ({
      schema: 1, experimental: true, intervalMinutes: 15, horizonHours: 6,
      referenceAt: new Date(reference).toISOString(), generatedAt: new Date(reference + 1000).toISOString(),
      observation: { timestamp: new Date(reference).toISOString(), level: 12 },
      models: [{ id: 'radar_arvores_live_candidate', label: 'Modelo de previsão', points: Array.from({ length: 6 }, (_, i) => ({ timestamp: new Date(reference + (i + 1) * 3600000).toISOString(), level: 12 + i })) }],
    });
    const previousMucum = fixture(current - 3600000);
    const previous = JSON.stringify({ ...previousMucum, encantado: { retired: true }, 'santa-tereza': { retired: true }, stationErrors: { encantado: 'unavailable' } });
    await writeFile(path.join(dir, 'latest.json'), previous);
    // Even a valid-looking result file cannot be published when inputs are missing.
    await writeFile(path.join(dir, 'result.json'), JSON.stringify(fixture(current)));
    const fake = (staleAttempt = false, mismatchedShadow = false) => `
      const fs = require('node:fs');
      const crypto = require('node:crypto');
      const args = process.argv;
      const state = args[args.indexOf('--state')+1];
      const attemptId = args[args.indexOf('--attempt-id')+1];
      const referenceAt = args[args.indexOf('--reference')+1];
      fs.mkdirSync(state+'/archive/blobs', {recursive:true});
      fs.mkdirSync(state+'/archive/pending', {recursive:true});
      const objects = ['runtime', 'attempt'].map(role => {
        const body = Buffer.from(role+'-'+attemptId);
        const sha256 = crypto.createHash('sha256').update(body).digest('hex');
        fs.writeFileSync(state+'/archive/blobs/'+sha256+'.tar.gz', body);
        return {key:'projection/blobs/'+sha256+'.tar.gz',sha256,bytes:body.length,role};
      });
      fs.writeFileSync(state+'/archive/pending/'+attemptId+'.json', JSON.stringify({
        schema:'radar-archive-receipt/v1',attemptId,referenceAt,status:'waiting_for_data',
        generatedAt:null,objects,missing:['Vazão da mesma hora ausente']
      }));
      fs.writeFileSync(state+'/refresh-status.json', JSON.stringify({status:'waiting_for_data',
        attemptId:${staleAttempt ? "'old-attempt'" : "args[args.indexOf('--attempt-id')+1]"},
        archiveReceiptKey:'projection/receipts/'+attemptId+'.json',
        checkedReferenceAt:referenceAt, referenceAt, missing:['Vazão da mesma hora ausente'],
        shadow:{status:'calculated',generatedAt:new Date().toISOString(),referenceAt,
          archiveReceiptKey:${mismatchedShadow ? "'projection/receipts/another-attempt.json'" : "'projection/receipts/'+attemptId+'.json'"},modelVersion:'mucum-hydrometry-shadow-v1',
          points:[{level:99}],sources:[{private:'internal'}],reason:'internal diagnostic'}}));
    `;
    await writeFile(script, fake());
    const { refreshProjection, readProjection, readProjectionRefreshState } = await import('../lib/projection-server.ts');
    assert.deepEqual(await readProjection(), previousMucum);
    const waiting = await refreshProjection();
    assert.equal(waiting.status, 'waiting_for_data');
    assert.deepEqual(waiting.missing, ['Vazão da mesma hora ausente']);
    assert.equal(waiting.shadow?.status, 'calculated');
    assert.equal(waiting.shadow?.referenceAt, new Date(current).toISOString());
    assert.ok(waiting.shadow?.archiveReceiptKey.startsWith('projection/receipts/'));
    assert.deepEqual(Object.keys(waiting.shadow!).sort(), ['archiveReceiptKey','generatedAt','modelVersion','referenceAt','status']);
    const waitingState = await readProjectionRefreshState();
    assert.equal(waitingState?.status, 'waiting_for_data');
    assert.ok(Number.isFinite(Date.parse(waitingState!.checkedAt)));
    assert.deepEqual(waitingState?.shadow, waiting.shadow);
    assert.equal(await readFile(path.join(dir, 'latest.json'), 'utf8'), previous);
    await assert.rejects(readFile(path.join(dir, 'rounds', new Date(current).toISOString()+'.json')), /ENOENT/);
    await writeFile(script, fake(true));
    await assert.rejects(refreshProjection(), /Invalid refresh attempt/);
    assert.equal((await readProjectionRefreshState())?.status, 'failed');
    assert.equal((await readProjectionRefreshState())?.shadow, undefined);
    assert.equal(await readFile(path.join(dir, 'latest.json'), 'utf8'), previous);
    await writeFile(script, fake(false, true));
    assert.equal((await refreshProjection()).shadow, undefined, 'Another receipt cannot authorize shadow metadata');
    await writeFile(script, fake().replaceAll("status:'waiting_for_data'", "status:'failed'") + '\nprocess.exit(1);');
    await assert.rejects(refreshProjection(), /Projection calculation failed/);
    const failedWithArchivedShadow = await readProjectionRefreshState();
    assert.equal(failedWithArchivedShadow?.status, 'failed');
    assert.equal(failedWithArchivedShadow?.shadow?.status, 'calculated');
    assert.equal(await readFile(path.join(dir, 'latest.json'), 'utf8'), previous);
    const activeModel = fixture(current);
    activeModel.models[0].id = 'radar_mucum_hydrometry_v1';
    await writeFile(path.join(dir, 'latest.json'), JSON.stringify({ ...activeModel, station: 'mucum',
      modelVersion: 'mucum-hydrometry-public-v1', modelSha256: 'a'.repeat(64),
      archiveReceiptKey: 'projection/receipts/already-published.json' }));
    process.env.PROJECTION_PYTHON = '/must-not-run-again';
    assert.equal((await refreshProjection()).status, 'already_calculated');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
