import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

test('publica hora completa atrasada com alvos futuros e impede regressão da referência', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'projection-delayed-'));
  process.env.MONITORA_DATA_DIR = root;
  process.env.PROJECTION_RUNTIME_DIR = root;
  process.env.PROJECTION_PYTHON = process.execPath;
  delete process.env.OBJECT_STORAGE_URL;
  try {
    const dir = path.join(root, 'projection');
    const script = path.join(root, 'scripts/hydro_site_projection.py');
    await mkdir(path.dirname(script), { recursive: true });
    await mkdir(dir);
    const fake = (offset: number) => `
      const fs = require('node:fs');
      const crypto = require('node:crypto');
      const args = process.argv;
      const state = args[args.indexOf('--state')+1];
      const attemptId = args[args.indexOf('--attempt-id')+1];
      const checkedReferenceAt = args[args.indexOf('--reference')+1];
      if(args.includes('--after-reference')) throw new Error('Legacy model must allow migration at the same reference');
      const reference = Date.parse(checkedReferenceAt) + ${offset} * 3600000;
      const referenceAt = new Date(reference).toISOString();
      const generatedAt = new Date().toISOString();
      const first = Math.floor((Date.parse(generatedAt)-reference)/3600000)+1;
      const result = {schema:1, experimental:true, intervalMinutes:15, horizonHours:6,
        forecastStartLeadHours:first,referenceAt,generatedAt,
        observation:{timestamp:referenceAt,level:12},models:[{id:'radar_arvores_live_candidate',label:'Modelo',
          points:Array.from({length:7-first},(_,i)=>({timestamp:new Date(reference+(first+i)*3600000).toISOString(),level:12}))}]};
      fs.mkdirSync(state+'/archive/blobs', {recursive:true});
      fs.mkdirSync(state+'/archive/pending', {recursive:true});
      const objects = ['runtime','attempt'].map(role=>{
        const body=Buffer.from(role+'-'+attemptId),sha256=crypto.createHash('sha256').update(body).digest('hex');
        fs.writeFileSync(state+'/archive/blobs/'+sha256+'.tar.gz',body);
        return {key:'projection/blobs/'+sha256+'.tar.gz',sha256,bytes:body.length,role};
      });
      fs.writeFileSync(state+'/archive/pending/'+attemptId+'.json',JSON.stringify({
        schema:'radar-archive-receipt/v1',attemptId,referenceAt,status:'calculated',generatedAt,objects}));
      fs.writeFileSync(state+'/refresh-status.json',JSON.stringify({status:'calculated',attemptId,referenceAt,
        checkedReferenceAt,generatedAt,archiveReceiptKey:'projection/receipts/'+attemptId+'.json'}));
      fs.writeFileSync(state+'/result.json',JSON.stringify(result));
    `;
    await writeFile(script, fake(-1));
    const { refreshProjection } = await import('../lib/projection-server.ts');
    const result = await refreshProjection();
    assert.equal(result.status, 'published');
    assert.equal(Date.parse(result.checkedReferenceAt!) - Date.parse(result.referenceAt), 3600000);
    const published = await readFile(path.join(dir, 'latest.json'), 'utf8');
    assert.equal(JSON.parse(published).models[0].points.length, 5);
    for (const key of ['encantado', 'santa-tereza', 'stationErrors']) {
      assert.equal(Object.hasOwn(JSON.parse(published), key), false, key);
    }
    await writeFile(script, fake(-2));
    await assert.rejects(refreshProjection(), /Invalid selected reference/);
    assert.equal(await readFile(path.join(dir, 'latest.json'), 'utf8'), published);
    await writeFile(script, fake(-4));
    await assert.rejects(refreshProjection(), /Invalid selected reference/);
    assert.equal(await readFile(path.join(dir, 'latest.json'), 'utf8'), published);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
