"""Bounded public ANA/ONS collection for a Radar research dataset, no fitting."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
from pathlib import Path
import csv
import hashlib
import json
import math
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/radar-insumos-2024-hidrologia-20260921'
OLD=ROOT/'outputs/historico-cheias-mucum'
ENDPOINT='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais'
WINDOWS=[('2024-03-29','2024-03-31'),('2024-04-01','2024-04-30'),('2024-05-01','2024-05-01')]
FIELDS=['NivelFinal','VazaoFinal','ChuvaFinal','ChuvaAcumAdotada']


def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def number(value):
    try:x=float(value)
    except (TypeError,ValueError):return None
    return x if math.isfinite(x) else None


def fetch(job):
    name,url,extra=job
    item=dict(file='raw/'+name,url=url,requested_at_utc=now(),**extra)
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Radar-public-history-research/1.0'})
        with urllib.request.urlopen(req,timeout=45) as response:
            body=response.read(16*1024*1024+1)
            item.update(http_status=response.status,headers=dict(response.headers))
        if len(body)>16*1024*1024:raise ValueError('Response exceeds bounded16MiB')
        path=OUT/item['file'];path.write_bytes(body)
        item.update(bytes=len(body),sha256=sha(path),status='downloaded')
    except Exception as error:
        item.update(status='failed',error=f'{type(error).__name__}: {error}')
    item['collected_at_utc']=now()
    return item


def audit_ana(item):
    path=ROOT/item['source_reference'] if item.get('source_reference') else OUT/item['file']
    assert sha(path)==item['sha256']
    tree=ET.parse(path).getroot()
    errors=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='Error' and e.text]
    if errors:return dict(item,status='source_error',source_errors=errors),[]
    rows=[];seen=set();outside=0
    for el in tree.iter():
        if el.tag.split('}')[-1]!='DadosHidrometereologicos':continue
        r={c.tag.split('}')[-1]:c.text for c in el}
        at=datetime.fromisoformat(r['DataHora'])
        assert at.tzinfo is None
        if r.get('CodEstacao')!=item['station']:raise ValueError('Station mismatch')
        if not item['subset_start']<=at.date().isoformat()<=item['subset_end']:
            outside+=1;continue
        if at in seen:raise ValueError('Duplicate station/time needs explicit review')
        seen.add(at)
        r.update(source_file=str(path.relative_to(ROOT)),source_sha256=item['sha256'])
        rows.append(r)
    return dict(item,status='parsed' if rows else 'no_data',rows_retained=len(rows),rows_outside_subset=outside),rows


def main():
    OUT.mkdir(exist_ok=False);(OUT/'raw').mkdir();(OUT/'stations').mkdir()
    protocol=ROOT/'docs/radar-inputs-2024-collection-protocol.json'
    (OUT/'protocol.json').write_bytes(protocol.read_bytes())
    weights=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json'
    codes=sorted({c for group in json.loads(weights.read_text()) for c in group['weights']})
    assert len(codes)==27 and all(c in codes for c in ['86510000','86472000','86472600','86500000'])
    jobs=[];manifest=[]
    old=json.loads((OLD/'manifest.json').read_text())['requests']
    for station in codes:
        for start,end in WINDOWS:
            extra=dict(source='ANA',station=station,subset_start=start,subset_end=end)
            if station=='86510000':
                prior=next(r for r in old if r['start_inclusive'][:7]==start[:7])
                path=OLD/prior['raw_file'];assert sha(path)==prior['sha256']
                manifest.append(dict(extra,status='verified_reuse',source_reference=str(path.relative_to(ROOT)),
                    url=prior['url'],sha256=prior['sha256'],original_retrieved_at=prior['retrieved_at'],verified_at_utc=now()))
                continue
            params={'codEstacao':station,'dataInicio':datetime.fromisoformat(start).strftime('%d/%m/%Y'),
                    'dataFim':datetime.fromisoformat(end).strftime('%d/%m/%Y')}
            jobs.append((f'ana-{station}-{start}--{end}.xml',ENDPOINT+'?'+urllib.parse.urlencode(params),extra))
    for month in ['2024_03','2024_04']:
        url=f'https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_ho/DADOS_HIDROLOGICOS_HO_{month}.parquet'
        jobs.append((f'ons-{month}.parquet',url,dict(source='ONS',month=month)))
    old_ons=ROOT/'outputs/historico-vazoes-ceran'
    prior=next(r for r in json.loads((old_ons/'source-manifest.json').read_text()) if r.get('file')=='raw/ons-2024-05.parquet')
    path=old_ons/prior['file'];assert sha(path)==prior['sha256']
    manifest.append(dict(source='ONS',month='2024_05',status='verified_reuse',source_reference=str(path.relative_to(ROOT)),
                         url=prior['url'],sha256=prior['sha256'],verified_at_utc=now()))
    dump(OUT/'source-manifest.json',manifest)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(fetch,job) for job in jobs]
        for future in as_completed(futures):
            item=future.result();manifest.append(item)
            dump(OUT/'source-manifest.json',manifest)
            print(len(manifest)-4,'/',len(jobs),item.get('file'),item['status'],flush=True)
    datasets={c:[] for c in codes};parsed=[]
    for item in manifest:
        if item['source']!='ANA' or item['status']=='failed':parsed.append(item);continue
        try:
            meta,rows=audit_ana(item);datasets[item['station']].extend(rows);parsed.append(meta)
        except Exception as error:
            parsed.append(dict(item,status='parse_failed',parse_error=f'{type(error).__name__}: {error}'))
    manifest=parsed;dump(OUT/'source-manifest.json',manifest)
    summaries=[]
    for code,rows in datasets.items():
        rows.sort(key=lambda r:r['DataHora'])
        assert len({r['DataHora'] for r in rows})==len(rows)
        with (OUT/'stations'/f'ana-{code}-all-qc.jsonl').open('w') as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        for field in FIELDS:
            numeric=[r for r in rows if number(r.get(field)) is not None]
            approved=[r for r in numeric if r.get('CQ_'+field)=='Dado aprovado']
            compatible=[r for r in numeric if r.get('CQ_'+field) in ['Dado aprovado',None] and number(r[field])>=0 and (field!='ChuvaFinal' or number(r[field])<=150)]
            summaries.append(dict(station=code,field=field,records=len(rows),nominal_15min_slots=34*96,
                numeric=len(numeric),approved=len(approved),current_parser_compatible=len(compatible),
                numeric_without_qc=sum(r.get('CQ_'+field) is None for r in numeric),
                negative=sum(number(r[field])<0 for r in numeric),
                first_approved=approved[0]['DataHora'] if approved else None,
                last_approved=approved[-1]['DataHora'] if approved else None,
                qc_counts=json.dumps(dict(Counter(r.get('CQ_'+field) or 'MISSING_QC' for r in rows)),ensure_ascii=False)))
    with (OUT/'ana-coverage.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    dump(OUT/'collection.json',dict(completed_at_utc=now(),requests=len(jobs),reused=4,stations=len(codes),
        manifest_statuses=dict(Counter(x['status'] for x in manifest)),
        retained_ana_rows=sum(len(v) for v in datasets.values()),normalized_for_model=False,trained=False,promoted=False,
        code_sha256=sha(Path(__file__)),protocol_sha256=sha(protocol),rain_weights_sha256=sha(weights)))
    (OUT/'collector.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(json.loads((OUT/'collection.json').read_text()),indent=2),flush=True)


if __name__=='__main__':main()
