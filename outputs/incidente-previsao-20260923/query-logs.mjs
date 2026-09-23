import {execFileSync} from 'node:child_process';import {writeFileSync} from 'node:fs';
const auth=JSON.parse(execFileSync('node',['node_modules/wrangler/bin/wrangler.js','auth','token','--json'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}));
const body={queryId:'radar-projection-incident',dry:true,view:'events',timeframe:{from:Date.parse('2026-09-23T01:00:00Z'),to:Date.now()},limit:100,parameters:{datasets:['cloudflare-workers'],filters:[{key:'$workers.scriptName',operation:'eq',type:'string',value:'sofik-monitoramento-taquari'},{key:'$metadata.error',operation:'exists',type:'string'}],filterCombination:'and',orderBy:{value:'timestamp',order:'desc'},limit:100}};
const r=await fetch('https://api.cloudflare.com/client/v4/accounts/f695d3055326e4346d3954d5cf1c0a17/workers/observability/telemetry/query',{method:'POST',headers:{authorization:`Bearer ${auth.token}`,'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();
if(!r.ok){console.log(JSON.stringify({status:r.status,errors:j.errors}));process.exit(1);}
const events=j.result?.events;console.log(JSON.stringify({keys:Object.keys(j.result||{}),eventsType:typeof events,eventsKeys:Object.keys(events||{})}));
const list=Array.isArray(events)?events:events?.events||[];
const safe=list.map(e=>({timestamp:e.timestamp,level:e.source?.level,message:e.source?.message,metadata:e.source?.['$metadata']?{message:e.source['$metadata'].message,error:e.source['$metadata'].error}:null,keys:Object.keys(e)}));
writeFileSync('outputs/incidente-previsao-20260923/errors.json',JSON.stringify(safe,null,2));console.log(JSON.stringify(safe,null,2));
