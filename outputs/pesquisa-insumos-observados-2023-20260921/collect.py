"""Bounded8publicANArequests at most; own research folder only; no model work."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
wp=ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json';weights=json.loads(wp.read_text());chosen=[{'group':g['group'],'station':max(g['weights'],key=g['weights'].get),'weight':max(g['weights'].values())} for g in weights];codes=sorted(set(['86472000','86472600','86500000']+[x['station'] for x in chosen]));assert len(codes)<=8
(P/'raw').mkdir(exist_ok=True)
inventory={c:[str(p.relative_to(ROOT)) for p in sorted((ROOT/'outputs').glob(f'*/raw/ana-{c}*.xml')) if not p.is_relative_to(P)] for c in codes}
# Existing filename inventory reviewed before network:2024/2025/fresh only, no2023 station collection.
plan={'window_start':'2023-08-29','window_end':'2023-09-04','auxiliary_levels':['86472000','86472600','86500000'],'largest_rain_weights':chosen,'stations':codes,'max_get_requests':8,'weights_source':str(wp.relative_to(ROOT)),'weights_sha256':hashlib.sha256(wp.read_bytes()).hexdigest(),'existing_station_xml_files_reviewed':inventory,'existing_2023_sources_reused_by_reference':['outputs/historico-cheia-setembro-2023/README.md','outputs/viabilidade-historico-antigo-radar-20260921/README.md'],'note':'Do not query Muçum, ONS, NWP, or reconstruct unavailable forecasts. Existing relevant station2023XML not found in reviewed inventory.'}
(P/'collection-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
for code in codes:
    side=P/'raw'/f'ana-{code}.source.json';dest=P/'raw'/f'ana-{code}.xml'
    if side.exists():print(code,'recorded request, no repeat',flush=True);continue
    assert not dest.exists(),'Orphan response: inspect before retry'
    args={'codEstacao':code,'dataInicio':'29/08/2023','dataFim':'04/09/2023'};url='https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urlencode(args)
    r={'station':code,'url':url,'parameters':args,'requested_at_utc':datetime.now(timezone.utc).isoformat(),'status':'request_started'};side.write_text(json.dumps(r,indent=2)+'\n')
    try:
        try:
            with urlopen(Request(url,headers={'User-Agent':'Radar-public-history-research/1.0'}),timeout=45) as h:body=h.read(4*1024*1024+1);r.update(http_status=h.status,headers=dict(h.headers),response_url=h.url)
        except HTTPError as e:body=e.read();r.update(http_status=e.code,headers=dict(e.headers))
        if len(body)>4*1024*1024:raise ValueError('Bounded response exceeds4MiB')
        dest.write_bytes(body);r.update(status='response_preserved',collected_at_utc=datetime.now(timezone.utc).isoformat(),file=str(dest.relative_to(P)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    except Exception as e:r.update(status='request_failed',finished_at_utc=datetime.now(timezone.utc).isoformat(),error=str(e))
    side.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(code,r['status'],r.get('http_status'),r.get('bytes'),flush=True)
