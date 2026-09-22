"""Bounded public ANA acquisition; explicitly preregister before networking."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import parse_qs,urlparse,urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,hashlib,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def plan():
 assert not (P/'collection-plan.json').exists()
 wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json';lp=ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json';codes=sorted({c for g in json.loads(wp.read_text()) for c in g['weights']});assert len(codes)==27 and set(codes)=={r['station'] for r in json.loads(lp.read_text())['stations']}
 folder=ROOT/'outputs/pesquisa-insumos-observados-2020-20260921';reused=[];refs=[wp,lp,folder/'source-manifest.json']
 for r in json.loads((folder/'source-manifest.json').read_text()):
  f=folder/r['file'];assert sha(f)==r['sha256'];reused.append(dict(station=r['station'],start='2020-07-04',end='2020-07-13',source_path=str(f.relative_to(ROOT)),source_metadata=r,sha256=r['sha256'],status='verified_reuse'))
 eight={r['station'] for r in reused};assert len(eight)==8
 folder=ROOT/'outputs/historico-cheias-mucum'
 for name in ['ana-86510000-2020-06-01--2020-06-30','ana-86510000-2020-07-01--2020-07-20']:
  mp=folder/'raw'/(name+'.manifest.json');refs.append(mp);r=json.loads(mp.read_text());f=folder/r['raw_file'];assert sha(f)==r['sha256'];reused.append(dict(station='86510000',start=r['start_inclusive'],end=r['end_inclusive'],source_path=str(f.relative_to(ROOT)),source_metadata=r,sha256=r['sha256'],status='verified_reuse'))
 extra_root=ROOT/'outputs/pesquisa-hidrologica-2026-09-21';mp=extra_root/'sample-manifest.json';refs.append(mp);r=next(r for r in json.loads(mp.read_text()) if r['file']=='ana-86510000-09-07-2020.xml');f=extra_root/r['file'];assert sha(f)==r['sha256'];reused.append(dict(station='86510000',start='2020-07-09',end='2020-07-09',source_path=str(f.relative_to(ROOT)),source_metadata=r,sha256=r['sha256'],status='verified_reuse',purpose='overlap comparison; monthly source first; no repeat network'))
 jobs=[]
 for c in codes:
  windows=[] if c=='86510000' else [('2020-06-28','2020-07-03'),('2020-07-14','2020-07-20')] if c in eight else [('2020-06-28','2020-07-20')]
  for start,end in windows:
   params=dict(codEstacao=c,dataInicio=datetime.fromisoformat(start).strftime('%d/%m/%Y'),dataFim=datetime.fromisoformat(end).strftime('%d/%m/%Y'));jobs.append(dict(station=c,start=start,end=end,parameters=params,url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode(params),file=f'raw/ana-{c}-{start}--{end}.xml'))
 assert len(jobs)==34
 inventory=[str(f.relative_to(ROOT)) for f in sorted((ROOT/'outputs').rglob('*.xml')) if '2020' in str(f) and not f.is_relative_to(P)]
 dump(P/'collection-plan.json',dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),stations=codes,window=['2020-06-28','2020-07-20'],warmup=['2020-06-28','2020-06-30'],max_new_gets=36,planned_new_gets=34,no_automatic_retries=True,new_jobs=jobs,reused=reused,existing_2020_xml_inventory=inventory,reference_hashes={str(f.relative_to(ROOT)):sha(f) for f in refs},duplicate_policy='Compare ALL original fields on equal station/timestamp; identical duplicates retain one normalized row and all provenance. Conflicts preserved separately, never resolve automatically.',exclusions=['No2021/22 requests','No ONS/NWP','No fits or matrix','No operational mutations','No interpolation/rounding/zero filling']))
 print('Registered34GETs,11reusedXMLs including96-rowoverlap audit',flush=True)
def collect():
    p=json.loads((P/'collection-plan.json').read_text());assert len(p['new_jobs'])<=36;(P/'raw').mkdir(exist_ok=True)
    for j in p['new_jobs']:
        dest=P/j['file'];side=dest.with_suffix('.source.json')
        if side.exists():print(j['station'],'already recorded; no repeat',flush=True);continue
        assert not dest.exists(),'Orphan response: no automatic retry'
        r={**j,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'request_started','plan_sha256':sha(P/'collection-plan.json')};dump(side,r)
        try:
            try:
                with urlopen(Request(j['url'],headers={'User-Agent':'Radar-public-history-research/1.0'}),timeout=45) as h:body=h.read(8*1024*1024+1);r.update(http_status=h.status,headers=dict(h.headers),response_url=h.url)
            except HTTPError as e:body=e.read();r.update(http_status=e.code,headers=dict(e.headers))
            if len(body)>8*1024*1024:raise ValueError('Bounded response exceeds8MiB')
            dest.write_bytes(body);r.update(status='response_preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),source_path=str(dest.relative_to(ROOT)),bytes=len(body),sha256=sha(dest))
        except Exception as e:r.update(status='request_failed',finished_at_utc=datetime.now(timezone.utc).isoformat(),error=str(e))
        dump(side,r);print(j['station'],r['status'],r.get('http_status'),r.get('bytes'),flush=True)
if __name__=='__main__':
 if sys.argv[1:]==['--plan']:plan()
 elif sys.argv[1:]==['--collect']:collect()
 else:raise SystemExit('Use --plan or --collect explicitly')
