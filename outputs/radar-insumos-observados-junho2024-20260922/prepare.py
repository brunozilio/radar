from pathlib import Path
import json,hashlib,datetime as dt
R=Path(__file__).resolve().parent;W=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n')
lat=W/'outputs/auditoria-latencias-chuva-20260921/latencies.json'
stations=sorted(r['station'] for r in json.loads(lat.read_text())['stations']);assert len(stations)==len(set(stations))==27
central=['86510000','86472000','86472600','86500000'];assert set(central)<=set(stations)
windows=[{'id':'2024-06-12','start':'2024-06-12','end':'2024-06-21','warmup_end':'2024-06-14','central_start':'2024-06-15'}]
reuse=[]
for station in central:
 folder='pesquisa-mucum-junho2024-20260922' if station=='86510000' else 'pesquisa-montante-junho2024-20260922'
 p=W/f'outputs/{folder}/raw/ana-{station}-20240615-20240621.xml';rp=Path(str(p)+'.receipt.json');m=json.loads(rp.read_text());assert sha(p)==m['sha256']
 reuse.append({'station':station,'window':'2024-06-12','start':'2024-06-15','end':'2024-06-21','source_path':str(p.relative_to(W)),'receipt_path':str(rp.relative_to(W)),'sha256':sha(p),'receipt_sha256':sha(rp),'original_receipt':m})
new=[{'station':s,'window':'2024-06-12','start':'2024-06-12','end':'2024-06-14' if s in central else '2024-06-21'} for s in stations]
plan={'registered_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'ANA ALL-QC collection12–21June2024, warmup12–14, origins15–21; no matrix, model, forecast, ONS or meteorological requests','station_count':27,'stations':stations,'windows':windows,'new_request_limit':27,'new_requests':new,'reuse':reuse,'max_concurrency':2,'automatic_retries':0,'automatic_redirects':False,'weights_source':str(lat.relative_to(W)),'weights_sha256':sha(lat),'station_authority':'Exactly stations[] in frozen latencies.json, not expanded from names','cache_inventory':'Before network, searched pertinent source-manifest/plan/raw receipt files for12June2024; no extra applicable segment found. Reused all4central responses including CarreiroSemdados; verified hashes/receipts.','merge_order':'Each series chronological; reuse central response then newlyrequested warmup in source-manifest; no overwrite precedence: differing original dictionaries at same timestamp remain separately flagged.','merge_rule':'Only identical full original field dictionaries merge, preserving all source_references. No conflict resolution.','rules':['Keep all original QC/fields, emptyXML=null, XMLrecordindex1-based','No interpolation, rounding, timezone conversion or zero-fill','No new ONS/meteo requests; no fit, inference or featurematrix','Reused response timestamps/receipts preserve original acquisition times, not newGET times']}
dump(R/'plan.json',plan);print('Plan:',len(stations),'stations;',len(new),'new requests;',len(reuse),'reused responses')
