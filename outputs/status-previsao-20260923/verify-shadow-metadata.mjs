import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const dir=new URL('./',import.meta.url);
const state=JSON.parse(readFileSync(new URL('production-verification.json',dir)));
const shadow=state.publicState.refresh?.shadow;
if(!shadow){console.log('New refresh metadata not present yet.');process.exit(2);}
if(Object.keys(shadow).some(key=>!['status','generatedAt','referenceAt','archiveReceiptKey','modelVersion'].includes(key)))throw Error('Unexpected public shadow field');
const auth=JSON.parse(execFileSync('node',['node_modules/wrangler/bin/wrangler.js','auth','token','--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
const base='https://api.cloudflare.com/client/v4/accounts/f695d3055326e4346d3954d5cf1c0a17/r2/buckets/sofik-monitoramento-media/objects/';
const headers={authorization:`Bearer ${auth.token}`};
async function body(key){const r=await fetch(base+encodeURIComponent(key),{headers});if(!r.ok)throw Error('R2 verification failed: '+r.status);return Buffer.from(await r.arrayBuffer());}
const receiptBytes=await body(shadow.archiveReceiptKey),receipt=JSON.parse(receiptBytes);
if(shadow.archiveReceiptKey!==`projection/receipts/${receipt.attemptId}.json`)throw Error('Receipt identity mismatch');
const attempt=receipt.objects.find(o=>o.role==='attempt'),bytes=await body(attempt.key);
if(createHash('sha256').update(bytes).digest('hex')!==attempt.sha256||bytes.length!==attempt.bytes)throw Error('Archive hash mismatch');
writeFileSync(new URL('verified-attempt.tar.gz',dir),bytes);
writeFileSync(new URL('verified-receipt.json',dir),receiptBytes);
writeFileSync(new URL('public-shadow.json',dir),JSON.stringify(shadow,null,2)+'\n');
console.log(JSON.stringify({shadow,archiveHashVerified:true,receiptStatus:receipt.status,publicGeneratedAt:state.publicState.projection?.generatedAt}));
