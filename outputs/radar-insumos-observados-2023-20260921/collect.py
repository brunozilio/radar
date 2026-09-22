"""Preregister then collect at most27publicANArequests; immutable source reuse."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import parse_qs,urlparse,urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,hashlib,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[1];OLD=ROOT/'outputs/pesquisa-insumos-observados-2023-20260921';MUCUM=ROOT/'outputs/historico-cheia-setembro-2023'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def plan():
    assert not (P/'collection-plan.json').exists(),'Plan already registered; do not overwrite'
    wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json';lp=ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json';weights=json.loads(wp.read_text());codes=sorted({c for g in weights for c in g['weights']});assert set(codes)=={s['station'] for s in json.loads(lp.read_text())['stations']} and len(codes)==27
    reused=[]
    for r in json.loads((OLD/'source-manifest.json').read_text()):
        f=OLD/r['file'];assert sha(f)==r['sha256'];reused.append({'station':r['station'],'start':'2023-08-29','end':'2023-09-04','source_path':str(f.relative_to(ROOT)),'source_metadata':r,'sha256':r['sha256'],'status':'verified_reuse'})
    prior8={r['station'] for r in reused}
    for r in json.loads((MUCUM/'source-manifest.json').read_text()):
        if not r['file'].endswith('.xml'):continue
        f=MUCUM/r['file'];assert sha(f)==r['sha256'];q=parse_qs(urlparse(r['url']).query);d=lambda s:datetime.strptime(s,'%d/%m/%Y').date().isoformat();reused.append({'station':'86510000','start':d(q['dataInicio'][0]),'end':d(q['dataFim'][0]),'source_path':str(f.relative_to(ROOT)),'source_metadata':r,'sha256':r['sha256'],'status':'verified_reuse'})
    jobs=[]
    for c in codes:
        start,end=('2023-08-29','2023-08-31') if c=='86510000' else ('2023-09-05','2023-09-30') if c in prior8 else ('2023-08-29','2023-09-30')
        params={'codEstacao':c,'dataInicio':datetime.fromisoformat(start).strftime('%d/%m/%Y'),'dataFim':datetime.fromisoformat(end).strftime('%d/%m/%Y')};jobs.append({'station':c,'start':start,'end':end,'url':'https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode(params),'parameters':params,'file':f'raw/ana-{c}-{start}--{end}.xml'})
    assert len(jobs)==27 and len(reused)==11
    inventory=[str(f.relative_to(ROOT)) for f in sorted((ROOT/'outputs').glob('*/raw/ana-*.xml')) if '2023' in str(f) and not f.is_relative_to(P)]
    obj={'registered_at_utc':datetime.now(timezone.utc).isoformat(),'window':['2023-08-29','2023-09-30'],'warmup':['2023-08-29','2023-08-31'],'potential_origins':'September2023; no matrix or labels constructed','stations':codes,'max_new_gets':27,'no_retry_without_review':True,'new_jobs':jobs,'reused':reused,'existing2023_xml_inventory':inventory,'reference_hashes':{str(f.relative_to(ROOT)):sha(f) for f in [wp,lp,OLD/'source-manifest.json',MUCUM/'source-manifest.json']},'exclusions':['No NWP requests','No ONS request','No training/matrix/imputation','No HGE/ARNO','Literal timestamps and ALL QC retained']}
    dump(P/'collection-plan.json',obj);print('preregistered27jobs and11reusedXMLs',flush=True)
def collect():
    p=json.loads((P/'collection-plan.json').read_text());assert len(p['new_jobs'])<=27;(P/'raw').mkdir(exist_ok=True)
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
    if sys.argv[1:] == ['--plan']:plan()
    elif sys.argv[1:] == ['--collect']:collect()
    else:raise SystemExit('Use --plan first, then --collect; no implicit collection.')
