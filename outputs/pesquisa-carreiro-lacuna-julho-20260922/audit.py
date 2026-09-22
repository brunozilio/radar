from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter
import xml.etree.ElementTree as ET
import json,hashlib,csv
P=Path(__file__).resolve().parent;R=P.parents[1];reused={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def track(p):reused[str(p.relative_to(R))]=sha(p);return p
def ck(n,b):checks.append(dict(check=n,passed=bool(b)));assert b,n
def dump(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def records(path):
 return [(i,{x.tag.split('}')[-1]:x.text for x in el}) for i,el in enumerate((el for el in ET.parse(path).getroot().iter() if el.tag.split('}')[-1]=='DadosHidrometereologicos'),1)]
def main():
 manifest=json.loads((P/'request-manifest.json').read_text())
 ck('five requests under cap',len(manifest)==5)
 for r in manifest:ck('new body '+r['file'],sha(P/r['file'])==r['sha256'])
 path=P/'raw/ana-window.xml';new=records(path);ck('192 stationidentified',len(new)==192 and all(r['CodEstacao']=='86500000' for _,r in new))
 times=[r['DataHora'] for _,r in new];ck('unique',len(set(times))==192)
 expected=[(datetime(2026,7,21)+timedelta(minutes=15*i)).strftime('%Y-%m-%d %H:%M:%S') for i in range(192)]
 ck('literal complete two day quartergrid',sorted(times)==expected)
 with (P/'ana-all-fields-original.jsonl').open('w') as f:
  for i,r in new:f.write(json.dumps(dict(**r,provenance=dict(source_file='raw/ana-window.xml',source_sha256=sha(path),xml_record_index_1based=i)),ensure_ascii=False)+'\n')
 fields={}
 for field in ('NivelFinal','NivelManual','NivelSensor','NivelDisplay','VazaoFinal'):
  counter=Counter((r.get(field) is not None,r.get('CQ_'+field)) for _,r in new)
  fields[field]=[dict(value_present=present,qc_literal=qc,records=n) for (present,qc),n in counter.items()]
 approved=[r for _,r in sorted(new,key=lambda x:x[1]['DataHora']) if r.get('NivelFinal') is not None and r.get('CQ_NivelFinal')=='Dado aprovado']
 ck('four manual final',len(approved)==4 and all(r['NivelManual']==r['NivelFinal'] and r['CQ_NivelManual']=='Dado aprovado' for r in approved))
 ck('sensor192 rejected',all(r.get('NivelSensor') is not None and r.get('CQ_NivelSensor')=='Dado reprovado' for _,r in new))
 oldpath=track(R/'outputs/mucum-propagacao-2026-09-21/raw/ana-86500000.xml');old={r['DataHora']:(i,r) for i,r in records(oldpath)};differences=[]
 for i,r in new:
  if r['DataHora'] not in old:differences.append(dict(DataHora=r['DataHora'],old_record_missing=True));continue
  oldindex,prior=old[r['DataHora']]
  for key in set(r)|set(prior):
   if r.get(key)!=prior.get(key):differences.append(dict(DataHora=r['DataHora'],field=key,old=prior.get(key),new=r.get(key),old_record_index=oldindex,new_record_index=i))
 ck('old-new allfields identical',not differences)
 ck('fresh and old window membership',all(t in old for t in times))
 dump('ana-comparison.json',dict(records=192,fields=fields,approved_readings=approved,old_source_file=str(oldpath.relative_to(R)),old_sha256=sha(oldpath),all_fields_identical=True,differences=differences,units_note='Nivel fields use legacy cm convention already preserved; no conversion in ALL-QC records.',timestamp_note='DataHora literal has no offset; UTC-03 is existing pipeline assumption, not new endpoint certification.'))
 sace=list(csv.DictReader((P/'raw/sace-current.csv').open(),delimiter=';'));st=[r['data_hora_medicao'] for r in sace];inside=[r for r in sace if '2026-07-21'<=r['data_hora_medicao']<'2026-07-23']
 points=track(R/'outputs/santa-tereza-model-v1/sources/sace-points.json');point=next(x for x in json.loads(points.read_text())['features'] if x['properties']['id']==54)
 ck('SACE identity',point['properties']['sigla']=='86500000');ck('SACE no requested dates',not inside)
 dump('sace-coverage.json',dict(rows=len(sace),first_literal=min(st),last_literal=max(st),header=list(sace[0]),requested_window_rows=len(inside),point_metadata=point,point_source=str(points.relative_to(R)),notes=['Current rolling export outside requested dates is not proof there are no historical source records.','CSV lacks per-value QC, offset and explicit unit header. Point metadata GMT-3 does not prove historical export conversion.','Altitude260 is not proven zero-of-gauge elevation or valid datum.']))
 reusedpaths=['outputs/auditoria-lacunas-carreiro/README.md','outputs/diagnostico-extremos-radar-20260921/carreiro-source-check.json','outputs/pesquisa-curva-chave-carreiro/README.md','outputs/verificacao-contrato-temporal-mucum/README.md','outputs/verificacao-contrato-temporal-mucum/raw/sace-identify.js','outputs/verificacao-contrato-temporal-mucum/raw/sace-public-display.html','outputs/mucum-bacia-2026-09-21/raw/sace-54.csv','outputs/mucum-bacia-2026-09-21/raw/events-fetch-manifest.json','outputs/mucum-bacia-2026-09-21/raw/refresh-manifest.json','outputs/santa-tereza-model-v1/level-raw/86500000-sace.sgb.gov.br.txt']
 for rel in reusedpaths:track(R/rel)
 prior=json.loads((R/'outputs/mucum-bacia-2026-09-21/raw/events-fetch-manifest.json').read_text());failures=[r for r in prior if r.get('file') in ('station-86500000-2026-07-21.txt','station-86500000-2026-07-22.txt')]
 dump('sigma-prior-attempts.json',dict(previous_manifest='outputs/mucum-bacia-2026-09-21/raw/events-fetch-manifest.json',previous_records=failures,note='Earlier404metadata existed without retained response bodies. Current two explicit reprobes preserve bodies; they were avoidable repeats if earlier failure metadata had been inspected before collection, not automatic retries.'))
 dump('reused-source-hashes.json',reused)
 dump('verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks=checks,checks_count=len(checks),direct_requests=5,search_queries=4,approved_subhourly_alternative_recovered=False,old_all_fields_identical=True,authentication_or_messages=False,fit_or_pipeline_change=False))
 print('PASS',len(checks),'checks;192records,4approvedmanual,192rejectedsensor',len(sace),'SACErecentrows')
if __name__=='__main__':main()
