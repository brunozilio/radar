"""Bounded public research. Five requests, no retry/login; keep errors."""
from pathlib import Path
from datetime import datetime,timezone
import urllib.request,urllib.parse,urllib.error,json,hashlib
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
jobs=[
 ('sigma-20260721.txt','https://sigmameteorologia.com/produtos/stations/2026-07-21/86500000.txt','Public SIGMA republication; station/date path used in existing collector. Not independently government-owned.'),
 ('sigma-20260722.txt','https://sigmameteorologia.com/produtos/stations/2026-07-22/86500000.txt','Same known public dated archive contract.'),
 ('sace-current.csv','https://sace.sgb.gov.br/api/dados/taquari_54_cota.csv','Existing official SGB export, station54 linked to86500000 by preserved point metadata; may only be rolling recent data.'),
 ('ana-window.xml','https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?'+urllib.parse.urlencode(dict(codEstacao='86500000',dataInicio='21/07/2026',dataFim='22/07/2026')),'Known public ANA endpoint; compare current response/revision, not independent measurement.'),
 ('rs-bulletin.html','https://www3.estado.rs.gov.br/centro-de-monitoramento-da-defesa-civil-do-rs-atualiza-prognostico-de-resposta-hidrologica','Official state page discovered by bounded search; possible publication link, not presumed station series.')]
def main():
 assert not (P/'request-manifest.json').exists()
 existing=[p for p in (R/'outputs').rglob('*86500000*') if p.is_file() and P not in p.parents]
 relevant=[p for p in existing if '2026-07-21' in p.name or '2026-07-22' in p.name]
 assert not relevant,'Inspect/reuse matching cache before requesting'
 (P/'cache-inventory.json').write_text(json.dumps(dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),station_filename_count=len(existing),matching_date_files=[],note='Existing bulk ANA XML and SACE rolling exports inspected separately and reused; no station date file July21/22 found.'),indent=2)+'\n')
 (P/'plan.json').write_text(json.dumps(dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),max_direct_requests=6,planned_requests=5,max_search_queries=4,search_queries_used=4,no_retries=True,no_auth=True,no_fill=True,requests=[dict(file=n,url=u,reason=r) for n,u,r in jobs]),indent=2)+'\n')
 manifest=[]
 for name,url,reason in jobs:
  record=dict(file='raw/'+name,url=url,reason=reason,started_at_utc=datetime.now(timezone.utc).isoformat())
  req=urllib.request.Request(url,headers={'User-Agent':'Radar-public-research/1.0','Referer':'https://sigmameteorologia.com/nowcasting/' if 'sigma' in url else url})
  try:
   response=urllib.request.urlopen(req,timeout=35);body=response.read();record.update(status=response.status,response_url=response.geturl(),headers=dict(response.headers))
  except urllib.error.HTTPError as e:
   body=e.read();record.update(status=e.code,response_url=e.geturl(),headers=dict(e.headers),http_error=str(e))
  except Exception as e:body=b'';record.update(transport_error=str(e))
  (P/'raw'/name).write_bytes(body);record.update(received_at_utc=datetime.now(timezone.utc).isoformat(),bytes=len(body),sha256=sha(P/'raw'/name));manifest.append(record)
  (P/'request-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(name,record.get('status',record.get('transport_error')),len(body),flush=True)
if __name__=='__main__':main()
