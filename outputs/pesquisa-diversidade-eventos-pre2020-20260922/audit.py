from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
checks=[]
def check(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
plan=json.loads((P/'collection-plan.json').read_text());rows=[]
for j in plan['jobs']:
 p=P/j['file'];m=json.loads(p.with_suffix('.xml.source.json').read_text());root=ET.fromstring(p.read_bytes())
 check(j['start']+' hash',sha(p)==m['sha256']);check(j['start']+' pre-registered',plan['registered_at_utc']<m['requested_at_utc'])
 recs=[e for e in root.iter() if e.tag.split('}')[-1]=='DadosHidrometereologicos'];errors=[e.text for e in root.iter() if e.tag.split('}')[-1]=='Error']
 check(j['start']+' no rows explicitly',len(recs)==0);check(j['start']+' Sem dados',len(errors)==1 and 'Sem dados para esta estação' in errors[0]);check(j['start']+' HTTP200',m['http_status']==200)
 rows.append({**j,'http_status':m['http_status'],'sha256':m['sha256'],'collected_at_utc':m['completed_at_utc'],'classification':'provider_sem_dados_not_network_failure','provider_errors':errors,'records_all_qc':len(recs),'approved_levels':0,'suspect_levels':0,'rejected_levels':0,'empty_level_rows':0,'exact_hour_levels':0,'quarter_hour_levels':0,'requested_days':7,'quarter_hour_schedule_reference':672,'hourly_schedule_reference':168,'gap':'entire queried window unavailable at this endpoint; expected sampling frequency not established','record_qc':'no records, therefore no fieldQC to inspect; absence is not rejectedQC or numericzero','timestamp_timezone':'not returned/not verifiable','duplicate_records':0,'conflicting_records':0})
dump(P/'probe-results.json',rows)
new=[]
for m in sorted(P.glob('**/*.source.json')):
 d=json.loads(m.read_text());p=P/d['file'];check(str(p.relative_to(P))+' bodyhash',p.exists() and sha(p)==d.get('sha256'));new.append(d)
dump(P/'new-source-manifest.json',new)
paths=['outputs/pesquisa-cheias-2021-2022-20260921/sources/sgb-2022.pdf','outputs/pesquisa-cheias-2021-2022-20260921/source-manifest.json','outputs/historico-cheias-mucum/documentation/sgb-mucum-cheia2020-artigo.pdf','outputs/historico-cheias-mucum/documentation/sgb-mucum-cheia2020-artigo.txt','outputs/historico-cheias-mucum/documentation/reference-investigation-report.md','outputs/historico-cheias-mucum/documentation/reference-investigation-manifest.json','outputs/pesquisa-referencia-legacy-20260921/README.md','outputs/pesquisa-armazenamento-ceran/README.md','outputs/pesquisa-armazenamento-ceran/reused-source-manifest.json']
dump(P/'reused-source-manifest.json',[{'file':x,'sha256':sha(R/x),'bytes':(R/x).stat().st_size} for x in paths])
events=[]
for x in rows:
 y=x['start'][:4];events.append({'year':int(y),'candidate_start':x['start'],'candidate_end':x['end'],'basis':x['basis'],'station':'86510000','ana_probe':x['file'],'ana_status':x['classification'],'eligible_hourly_dataset':False,'gauge_continuity_to_2026':'unverified','historical_availability_at_forecast_issue':'unverified','used_for_fit_or_inference':False,'limitations':{'2011':'Date21July appears in official-hosted research quoting anotherstudy; samePDF also says11July. RawAVADAN not retrieved; no certified Muçumpeakdate.','2015':'OfficialCivilDefence page indexed; directGET404 preserved. Regionalimpact not stationpeak.','2017':'SGB26May marks Muçummaintenance and operationalforecasts testing; no Muçumobservedlevel in bulletin.'}[y]})
events.append({'year':2019,'candidate_start':None,'candidate_end':None,'status':'event_date_unresolved_no_probe','basis':'SGB2022report p23/printed19 table3 lists0observedevents and0bulletins2019 withinSAH accounting. Not universal absenceofcheias.','used_for_fit_or_inference':False})
dump(P/'candidate-inventory.json',events)
dump(P/'verification.json',{'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,'ana_get_requests':3,'ana_records_recovered':0,'new_document_requests':4,'document_http_statuses':[r['http_status'] for r in new if r['file'].startswith('sources/')],'normalization':False,'training_or_inference':False})
print('PASS',len(checks),'checks;3Semdados;0records')
