// Read-only extraction from the authorized production R2 bucket. Never prints credentials.
import {execFileSync} from 'node:child_process';
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const dir=path.dirname(fileURLToPath(import.meta.url));
const smoke=JSON.parse(readFileSync(path.join(dir,'runtime-smoke-proof.json')));
const localReceipt=JSON.parse(readFileSync(smoke.receipt));
const expectedRuntime=localReceipt.objects.find(o=>o.role==='runtime').sha256;
const before=JSON.parse(readFileSync(path.join(dir,'production-before.json'))).checkedAt;
const auth=JSON.parse(execFileSync('node',['node_modules/wrangler/bin/wrangler.js','auth','token','--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
const base='https://api.cloudflare.com/client/v4/accounts/f695d3055326e4346d3954d5cf1c0a17/r2/buckets/sofik-monitoramento-media/objects';
const headers={authorization:`Bearer ${auth.token}`};
const sha=b=>createHash('sha256').update(b).digest('hex');
async function list(prefix){
 const r=await fetch(base+'?prefix='+encodeURIComponent(prefix)+'&per_page=1000',{headers});
 const j=await r.json();if(!r.ok||!j.success)throw Error('R2 listing failed: '+r.status);
 if(j.result_info?.is_truncated)throw Error('Pagination required');
 return j.result;
}
async function body(key){
 const r=await fetch(base+'/'+encodeURIComponent(key),{headers});
 if(!r.ok)throw Error('R2 object failed: '+r.status);
 return Buffer.from(await r.arrayBuffer());
}
const candidates=(await list('projection/receipts/')).filter(r=>r.last_modified>before).sort((a,b)=>b.last_modified.localeCompare(a.last_modified));
let found=false;
for(const metadata of candidates){
 const receiptBody=await body(metadata.key), receipt=JSON.parse(receiptBody);
 if(receipt.objects.find(o=>o.role==='runtime')?.sha256!==expectedRuntime)continue;
 const output=path.join(dir,'production-archive',receipt.attemptId);mkdirSync(output,{recursive:true});
 const objects=[];
 for(const object of receipt.objects){
  const bytes=await body(object.key);
  if(sha(bytes)!==object.sha256||bytes.length!==object.bytes)throw Error('Archive integrity failure');
  const objectMetadata=(await list(object.key)).find(o=>o.key===object.key);
  if(!objectMetadata?.last_modified)throw Error('Object archival timestamp unavailable');
  writeFileSync(path.join(output,object.role+'.tar.gz'),bytes);
  objects.push({...object,lastModified:objectMetadata.last_modified});
 }
 const proof={checkedAt:new Date().toISOString(),receiptKey:metadata.key,receiptSha256:sha(receiptBody),receiptLastModified:metadata.last_modified,expectedRuntimeSha256:expectedRuntime,objects};
 writeFileSync(path.join(output,'receipt.json'),receiptBody);
 writeFileSync(path.join(output,'verified-remote.json'),JSON.stringify(proof,null,2)+'\n');
 writeFileSync(path.join(dir,'verified-shadow-archive.json'),JSON.stringify({directory:output,...proof},null,2)+'\n');
 console.log(JSON.stringify({directory:output,receipt:metadata.key,receiptLastModified:metadata.last_modified,status:receipt.status,hashesVerified:true}));
 found=true;break;
}
if(!found){console.log('No archived attempt from the new frozen runtime yet.');process.exitCode=2;}
