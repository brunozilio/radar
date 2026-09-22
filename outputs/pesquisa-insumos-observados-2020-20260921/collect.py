"""Bounded8publicANArequests at most; own research folder only; no model work."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,hashlib,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json';weights=json.loads(wp.read_text());chosen=[{'group':g['group'],'station':max(g['weights'],key=g['weights'].get),'weight':max(g['weights'].values())} for g in weights];codes=sorted(set(['86472000','86472600','86500000']+[x['station'] for x in chosen]));assert len(codes)<=8
(P/'raw').mkdir(exist_ok=True)
inventory={c:[str(p.relative_to(ROOT)) for p in sorted((ROOT/'outputs').glob(f'*/raw/ana-{c}*.xml')) if not p.is_relative_to(P)] for c in codes}
# Inspect the date extent of every inventoried XML before deciding to request.
review=[]
for c,files in inventory.items():
    for name in files:
        body=(ROOT/name).read_bytes();tree=ET.fromstring(body)
        times=[e.text for e in tree.iter() if e.tag.split('}')[-1]=='DataHora' and e.text]
        overlap=[t for t in times if '2020-07-04'<=t[:10]<='2020-07-13']
        review.append({'station':c,'file':name,'sha256':hashlib.sha256(body).hexdigest(),'rows_with_time':len(times),'first':min(times) if times else None,'last':max(times) if times else None,'in_requested_window':len(overlap)})
        assert not overlap,'Potential reusable source found; inspect before requesting'
(P/'prior-source-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
plan={'window_start':'2020-07-04','window_end':'2020-07-13','auxiliary_levels':['86472000','86472600','86500000'],'largest_rain_weights':chosen,'stations':codes,'max_get_requests':8,'weights_source':str(wp.relative_to(ROOT)),'weights_sha256':hashlib.sha256(wp.read_bytes()).hexdigest(),'existing_station_xml_files_reviewed':inventory,'existing_2020_sources_reused_by_reference':['outputs/historico-cheias-mucum/README.md','outputs/historico-vazoes-ceran/README.md','outputs/viabilidade-historico-antigo-radar-20260921/README.md'],'note':'Do not query Muçum, ONS, NWP, or reconstruct unavailable forecasts. Date inspection found no overlapping2020 records in the inventoried station XMLs. This is only a feasibility probe of8stations, not complete regional rain or a training matrix.'}
(P/'collection-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
for code in codes:
    side=P/'raw'/f'ana-{code}.source.json';dest=P/'raw'/f'ana-{code}.xml'
    if side.exists():print(code,'recorded request, no repeat',flush=True);continue
    assert not dest.exists(),'Orphan response: inspect before retry'
    args={'codEstacao':code,'dataInicio':'04/07/2020','dataFim':'13/07/2020'};url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode(args)
    r={'station':code,'url':url,'parameters':args,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'request_started'};side.write_text(json.dumps(r,indent=2)+'\n')
    try:
        try:
            with urlopen(Request(url,headers={'User-Agent':'Radar-public-history-research/1.0'}),timeout=45) as h:body=h.read(4*1024*1024+1);r.update(http_status=h.status,headers=dict(h.headers),response_url=h.url)
        except HTTPError as e:body=e.read();r.update(http_status=e.code,headers=dict(e.headers))
        if len(body)>4*1024*1024:raise ValueError('Bounded response exceeds4MiB')
        dest.write_bytes(body);r.update(status='response_preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),file=str(dest.relative_to(P)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    except Exception as e:r.update(status='request_failed',finished_at_utc=datetime.now(timezone.utc).isoformat(),error=str(e))
    side.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(code,r['status'],r.get('http_status'),r.get('bytes'),flush=True)
