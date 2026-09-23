import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
const dir=new URL('./',import.meta.url);
const snapshot=JSON.parse(readFileSync(new URL('production-verification.json',dir)));
const forecast=snapshot.publicState.projection;
if(forecast?.models?.[0]?.id!=='radar_mucum_hydrometry_v1'){console.log('Hydrometric public issue not present yet.');process.exit(2);}
if(forecast.modelVersion!=='mucum-hydrometry-public-v1'||forecast.experimental!==true||forecast.rainRequired!==false)throw Error('Unexpected public model contract');
const pending=new URL('package-state/archive/pending/',dir);
const localReceipt=JSON.parse(readFileSync(new URL(readdirSync(pending)[0],pending)));
const expectedRuntime=localReceipt.objects.find(o=>o.role==='runtime').sha256;
const auth=JSON.parse(execFileSync('node',['node_modules/wrangler/bin/wrangler.js','auth','token','--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
const base='https://api.cloudflare.com/client/v4/accounts/f695d3055326e4346d3954d5cf1c0a17/r2/buckets/sofik-monitoramento-media/objects/';
const headers={authorization:`Bearer ${auth.token}`};
async function body(key){const r=await fetch(base+encodeURIComponent(key),{headers});if(!r.ok)throw Error('R2 verification failed: '+r.status);return Buffer.from(await r.arrayBuffer());}
const receiptBytes=await body(forecast.archiveReceiptKey),receipt=JSON.parse(receiptBytes);
if(receipt.status!=='calculated'||receipt.generatedAt!==forecast.generatedAt||receipt.referenceAt!==forecast.referenceAt)throw Error('Published issue not bound to its receipt');
if(receipt.objects.find(o=>o.role==='runtime')?.sha256!==expectedRuntime)throw Error('Published runtime differs from tested package');
const attempt=receipt.objects.find(o=>o.role==='attempt'),bytes=await body(attempt.key);
if(createHash('sha256').update(bytes).digest('hex')!==attempt.sha256||bytes.length!==attempt.bytes)throw Error('Public archive checksum mismatch');
writeFileSync(new URL('verified-public-attempt.tar.gz',dir),bytes);
writeFileSync(new URL('verified-public-receipt.json',dir),receiptBytes);
writeFileSync(new URL('public-forecast.json',dir),JSON.stringify(forecast,null,2)+'\n');
console.log(JSON.stringify({generatedAt:forecast.generatedAt,referenceAt:forecast.referenceAt,model:forecast.models[0].id,points:forecast.models[0].points,receipt:forecast.archiveReceiptKey,archiveHashVerified:true,runtimeMatchesLocalPackage:true}));
