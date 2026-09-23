import {execFileSync} from 'node:child_process';
import {writeFileSync,readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const auth=JSON.parse(execFileSync('node',['node_modules/wrangler/bin/wrangler.js','auth','token','--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
const account='f695d3055326e4346d3954d5cf1c0a17';
const base=`https://api.cloudflare.com/client/v4/accounts/${account}`;
const headers={authorization:`Bearer ${auth.token}`};
async function get(route) {
 const r=await fetch(base+route,{headers});const j=await r.json();
 if(!r.ok||!j.success)throw new Error(`Cloudflare ${route}: ${r.status}`);
 return j.result;
}
const deployments=await get('/workers/scripts/sofik-monitoramento-taquari/deployments');
const app=await get('/containers/applications/a039a738-b702-4f15-b273-7e22b92be8d8');
const instances=JSON.parse(execFileSync('node',['node_modules/wrangler/bin/wrangler.js','containers','instances',app.id,'--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
const r2='/r2/buckets/sofik-monitoramento-media/objects';
const response=await fetch(base+r2+'/'+encodeURIComponent('projection/latest.json'),{headers});
if(!response.ok)throw new Error(`Latest projection: ${response.status}`);
const bytes=Buffer.from(await response.arrayBuffer());
const latest=JSON.parse(bytes);
const receipts=await get(r2+'?prefix=projection%2Freceipts%2F&per_page=1000');
const publicResponse=await fetch('https://radar.brunozilio.com/api/projection');
const publicState=await publicResponse.json();
const runtime=readFileSync('projection-runtime/manifest.json');
const result={checkedAt:new Date().toISOString(),worker:{id:deployments.deployments?.[0]?.id,createdAt:deployments.deployments?.[0]?.created_on,versions:deployments.deployments?.[0]?.versions},
 application:{id:app.id,name:app.name,image:app.configuration?.image,maxInstances:app.max_instances,version:app.version},
 instances,latest:{referenceAt:latest.referenceAt,generatedAt:latest.generatedAt,modelVersion:latest.modelVersion,archiveReceiptKey:latest.archiveReceiptKey,sha256:createHash('sha256').update(bytes).digest('hex')},
 publicState,archiveReceipts:receipts.map(r=>({key:r.key,lastModified:r.last_modified})),
 localRuntimeManifestSha256:createHash('sha256').update(runtime).digest('hex')};
writeFileSync(new URL('./production-verification.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
