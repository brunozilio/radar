from pathlib import Path
import json,hashlib,datetime as dt
R=Path(__file__).resolve().parent;W=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n')
weights=W/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
stations=sorted({s for g in json.loads(weights.read_text()) for s in g['weights']})
assert len(stations)==27
windows=[{'id':'2018-08-27','start':'2018-08-27','end':'2018-09-05','warmup_end':'2018-08-29','central_start':'2018-08-30'}, {'id':'2018-09-27','start':'2018-09-27','end':'2018-10-06','warmup_end':'2018-09-29','central_start':'2018-09-30'}]
reuse=[]
for win in windows:
 for station in ['86510000','86472000','86472600','86500000']:
  if station=='86510000':
   p=W/'outputs/pesquisa-janelas-ineditas-20260922/raw'/f"ana-{win['central_start'].replace('-','')}-{win['end'].replace('-','')}.xml"
   rp=p.with_name(p.name+'.receipt.json')
  else:
   p=W/'outputs/pesquisa-montante-2018-20260922/raw'/f"ana-{station}-{win['central_start']}-{win['end']}.xml"
   rp=p.with_suffix('.receipt.json')
  m=json.loads(rp.read_text());assert sha(p)==m['sha256']
  reuse.append({'station':station,'window':win['id'],'start':win['central_start'],'end':win['end'],'source_path':str(p.relative_to(W)),'receipt_path':str(rp.relative_to(W)),'sha256':sha(p),'receipt_sha256':sha(rp),'original_receipt':m})
new=[]
for win in windows:
 for station in stations:
  new.append({'station':station,'window':win['id'],'start':win['start'],'end':win['warmup_end'] if station in ['86510000','86472000','86472600','86500000'] else win['end']})
assert len(new)==54 and len(reuse)==8
plan={'registered_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Observed ANA ALL-QC collection only; no matrix/model/fit/forecast/operational change','station_count':len(stations),'stations':stations,'windows':windows,'new_request_limit':54,'new_requests':new,'reuse':reuse,'max_concurrency':2,'automatic_retries':0,'automatic_redirects':False,'weights_source':str(weights.relative_to(W)),'weights_sha256':sha(weights),'cache_inventory':'Before requests, searched existing receipt/manifest/plan/reference files for literal and URL dates27/08/2018,27/09/2018; no pertinent extra cache found. Eight central-period XMLs verified against original receipts and reused, including four Sem dados bodies.','merge_rule':'Only records with exactly identical original field dictionaries may merge; retain all source references. Different records at same timestamp remain separate and flagged, never reconciled.','rules':['Preserve original timestamps, fields, QC, empty values and record indices1-based','Missing rain stays unknown, never zero-fill','No interpolation, resampling, timezone/datum assertion or latency adjustment','No NWP, ONS, HGE/ARNO or training','Preserve each attempted HTTP response and error without retry']}
dump(R/'plan.json',plan);print('Plan:',len(stations),'stations;',len(new),'new requests;',len(reuse),'reused responses')
