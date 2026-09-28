// Publish the already generated, archived forecast explicitly requested by the user.
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { validProjection, isHydrometricProjection } from '../../lib/projection.ts';

const dir = new URL('./', import.meta.url);
const bytes = readFileSync(new URL('package-state/result.json', dir));
const forecast = JSON.parse(bytes);
const receiptBytes = readFileSync(new URL('package-state/archive/pending/3ff483aa-1a3e-43cf-8ccd-2adc285165c4.json', dir));
const receipt = JSON.parse(receiptBytes);
const hash = body => createHash('sha256').update(body).digest('hex');
function assertReady() {
  if (!validProjection(forecast) || !isHydrometricProjection(forecast) ||
      receipt.status !== 'calculated' || receipt.generatedAt !== forecast.generatedAt ||
      Date.parse(receipt.referenceAt) !== Date.parse(forecast.referenceAt) ||
      forecast.archiveReceiptKey !== `projection/receipts/${receipt.attemptId}.json` ||
      Date.now() - Date.parse(forecast.generatedAt) > 3600000 ||
      Date.now() - Date.parse(forecast.referenceAt) > 3 * 3600000 ||
      forecast.models[0].points.some(point => Date.parse(point.timestamp) <= Date.now())) {
    throw Error('Generated forecast is not eligible for publication');
  }
}
assertReady();
const archivedForecast = execFileSync('tar', ['-xOzf', new URL(`package-state/archive/blobs/${receipt.objects.find(o => o.role === 'attempt').sha256}.tar.gz`, dir).pathname, 'forecast.json']);
if (JSON.stringify(JSON.parse(archivedForecast)) !== JSON.stringify(forecast)) throw Error('Archived forecast differs from publication');
const auth = JSON.parse(execFileSync('node', ['node_modules/wrangler/bin/wrangler.js', 'auth', 'token', '--json'], {encoding:'utf8', stdio:['ignore','pipe','pipe']}));
const base = 'https://api.cloudflare.com/client/v4/accounts/f695d3055326e4346d3954d5cf1c0a17/r2/buckets/sofik-monitoramento-media/objects/';
const headers = {authorization: `Bearer ${auth.token}`};
async function get(key, optional = false) {
  const response = await fetch(base + encodeURIComponent(key), {headers, signal:AbortSignal.timeout(30000)});
  if (optional && response.status === 404) return null;
  if (!response.ok) throw Error(`R2 read ${key}: HTTP ${response.status}`);
  return Buffer.from(await response.arrayBuffer());
}
async function put(key, body, mime) {
  const response = await fetch(base + encodeURIComponent(key), {method:'PUT', headers:{...headers,'content-type':mime}, body, signal:AbortSignal.timeout(60000)});
  if (!response.ok) throw Error(`R2 write ${key}: HTTP ${response.status}`);
  if (hash(await get(key)) !== hash(body)) throw Error(`R2 verification mismatch: ${key}`);
}
async function immutable(key, body, mime) {
  const existing = await get(key, true);
  if (existing) {
    if (hash(existing) !== hash(body)) throw Error(`Immutable collision: ${key}`);
  } else await put(key, body, mime);
}
function supersedes(previous) {
  return Date.parse(previous.referenceAt) > Date.parse(forecast.referenceAt) ||
    (isHydrometricProjection(previous) && Date.parse(previous.referenceAt) === Date.parse(forecast.referenceAt));
}
if (supersedes(JSON.parse(await get('projection/latest.json')))) {
  console.log('A matching or newer hydrometric forecast is already public.');
  process.exit(0);
}
for (const object of receipt.objects) {
  const blob = readFileSync(new URL(`package-state/archive/blobs/${object.sha256}.tar.gz`, dir));
  if (hash(blob) !== object.sha256 || blob.length !== object.bytes) throw Error(`Local archive mismatch: ${object.role}`);
  await immutable(object.key, blob, 'application/gzip');
}
await immutable(forecast.archiveReceiptKey, receiptBytes, 'application/json');
await immutable(`projection/issues/${forecast.generatedAt}.json`, bytes, 'application/json');
assertReady();
if (supersedes(JSON.parse(await get('projection/latest.json')))) {
  console.log('A matching or newer hydrometric forecast was published during archive upload.');
  process.exit(0);
}
await put(`projection/rounds/${new Date(forecast.referenceAt).toISOString()}.json`, bytes, 'application/json');
assertReady();
await put('projection/latest.json', bytes, 'application/json');
const proof = {publishedAt:new Date().toISOString(), generatedAt:forecast.generatedAt, referenceAt:forecast.referenceAt, model:forecast.models[0].id, archiveReceiptKey:forecast.archiveReceiptKey, sha256:hash(bytes), archiveVerified:true, publication:'Explicitly requested publication of already generated forecast; original input and calculation times preserved'};
writeFileSync(new URL('publication-proof.json',dir),JSON.stringify(proof,null,2)+'\n');
console.log(JSON.stringify(proof));
