from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,xml.etree.ElementTree as ET,calendar,csv
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def check(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
def jsonl(n,x):(P/n).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
def csvsave(n,x):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
windows={2011:('2011-07-18','2011-07-24'),2015:('2015-10-08','2015-10-14'),2017:('2017-05-24','2017-05-30')}
manifest=[];records=[];cells=[];requests=[]
for metap in sorted(P.glob('**/*.source.json')):
 m=json.loads(metap.read_text());p=P/m['file'];check(p.name+'sha',sha(p)==m['sha256']);manifest.append(m)
 if not m['file'].startswith('raw/'):continue
 root=ET.fromstring(p.read_bytes());rr=[e for e in root.iter() if e.tag.split('}')[-1]=='SerieHistorica'];ee=[e.text for e in root.iter() if e.tag.split('}')[-1]=='Error']
 check(p.name+'http200',m['http_status']==200)
 if p.name.startswith('month-'):
  plan=json.loads((P/'monthly-plan.json').read_text());check(p.name+'plan',plan['registered_at_utc']<m['requested_at_utc']);check(p.name+'rows',len(rr)==(3 if m['parameters']['nivelConsistencia']=='1' else 1) and not ee)
 else:
  plan=json.loads((P/'plan.json').read_text());check(p.name+'plan',plan['registered_at_utc']<m['requested_at_utc']);check(p.name+'explicitSemdados',not rr and len(ee)==1 and 'Sem dados' in ee[0])
 requests.append({'source_file':m['file'],'http_status':m['http_status'],'start':m['start'],'end':m['end'],'requested_consistency':m['parameters']['nivelConsistencia'],'records':len(rr),'provider_errors':ee,'classification':'monthly_records_returned' if rr else 'provider_sem_dados_for_week_filter_not_proof_of_absence'})
 for ix,e in enumerate(rr,1):
  fields={c.tag.split('}')[-1]:c.text for c in e};check(p.name+f'identity{ix}',fields['EstacaoCodigo']=='86510000' and fields['NivelConsistencia']==m['parameters']['nivelConsistencia']);dt=datetime.fromisoformat(fields['DataHora']);check(p.name+f'monthlydate{ix}',dt.day==1)
  rec={**fields,'_provenance':{'source_file':m['file'],'source_sha256':m['sha256'],'record_index_1based':ix,'record_tag':'SerieHistorica','collected_at_utc':m['finished_at_utc'],'url':m['url']}};records.append(rec)
  for day in range(1,calendar.monthrange(dt.year,dt.month)[1]+1):
   field=f'Cota{day:02d}';date=f'{dt.year}-{dt.month:02d}-{day:02d}';a,b=windows[dt.year]
   cells.append({'date_from_month_and_field':date,'clock_literal':fields['DataHora'][11:],'is_daily_mean':fields['MediaDiaria']=='1','record_DataHora_literal':fields['DataHora'],'record_DataIns_literal':fields.get('DataIns'),'NivelConsistencia':fields['NivelConsistencia'],'TipoMedicaoCotas':fields.get('TipoMedicaoCotas'),'field':field,'value_original_cm':fields.get(field),'value_field_present':field in fields,'status_original':fields.get(field+'Status'),'status_field_present':field+'Status' in fields,'inside_candidate_window':a<=date<=b,'source_file':m['file'],'source_sha256':m['sha256'],'record_index_1based':ix})
jsonl('records-original-fields.jsonl',records);jsonl('day-field-inventory.jsonl',cells);jsonl('candidate-window-cells.jsonl',[x for x in cells if x['inside_candidate_window']])
# Verify complete extraction roundtrip, without normalizing any original field.
for r in records:
 root=ET.fromstring((P/r['_provenance']['source_file']).read_bytes());rr=[e for e in root.iter() if e.tag.split('}')[-1]=='SerieHistorica'];raw={c.tag.split('}')[-1]:c.text for c in rr[r['_provenance']['record_index_1based']-1]}
 check('record fieldwise roundtrip',raw=={k:v for k,v in r.items() if k!='_provenance'})
summary=[];comparisons=[]
for year in windows:
 cc=[x for x in cells if int(x['date_from_month_and_field'][:4])==year];ww=[x for x in cc if x['inside_candidate_window']];rawinst=[x for x in ww if x['NivelConsistencia']=='1' and not x['is_daily_mean']];rd=[x for x in ww if x['NivelConsistencia']=='1' and x['is_daily_mean']];cd=[x for x in ww if x['NivelConsistencia']=='2']
 check(str(year)+'instant coverage',len(rawinst)==14 and all(x['value_original_cm'] is not None for x in rawinst));check(str(year)+'daily coverage',len(rd)==7 and len(cd)==7 and all(x['value_original_cm'] is not None for x in rd+cd));check(str(year)+'clocks',set(x['clock_literal'] for x in rawinst)=={'07:00:00','17:00:00'} and all(x['clock_literal']=='00:00:00' and x['is_daily_mean'] for x in rd+cd))
 peak=max(rawinst,key=lambda x:float(x['value_original_cm']));day_map={(x['date_from_month_and_field'],x['NivelConsistencia'],x['clock_literal']):x for x in cc}
 for x in [c for c in cc if c['NivelConsistencia']=='1' and c['is_daily_mean']]:
  date=x['date_from_month_and_field'];v=x['value_original_cm'];c=day_map[(date,'2','00:00:00')]['value_original_cm'];a=day_map[(date,'1','07:00:00')]['value_original_cm'];b=day_map[(date,'1','17:00:00')]['value_original_cm']
  diff=None if v is None or c is None else float(c)-float(v);mean_diff=None if any(z is None for z in (a,b,v)) else float(v)-(float(a)+float(b))/2
  if mean_diff is not None:check(date+'raw mean identity',mean_diff==0)
  comparisons.append({'date':date,'raw_daily_cm':v,'consistent_daily_cm':c,'consistent_minus_raw_cm':diff,'raw_mean_minus_7plus17_div2_cm':mean_diff,'inside_candidate_window':x['inside_candidate_window']})
 summary.append({'year':year,'window':windows[year],'monthly_records':sum(r['DataHora'].startswith(str(year)) for r in records),'monthly_value_fields_present':sum(x['value_original_cm'] is not None for x in cc),'monthly_absent_value_fields':sum(x['value_original_cm'] is None for x in cc),'window_instant_raw':len(rawinst),'window_raw_daily_means':len(rd),'window_consistent_daily_means':len(cd),'instant_clock_intervals_hours':[10,14],'window_raw_instant_status_histogram':dict(Counter(x['status_original'] if x['status_field_present'] else 'field_absent' for x in rawinst)),'window_consistent_status_histogram':dict(Counter(x['status_original'] for x in cd)),'window_peak_of_returned_raw_readings':peak,'DataIns_by_consistency':{qc:sorted({x['record_DataIns_literal'] for x in cc if x['NivelConsistencia']==qc}) for qc in ('1','2')}})
check('no duplicates within version cadence',len({(x['date_from_month_and_field'],x['clock_literal'],x['NivelConsistencia'],x['is_daily_mean']) for x in cells})==len(cells))
check('12 monthly source records',len(records)==12);check('372 calendar cells 357nonnull',len(cells)==372 and sum(x['value_original_cm'] is not None for x in cells)==357)
api=json.loads((P/'sources/new-api-v1-openapi.json').read_text());op=api['paths']['/EstacoesTelemetricas/HidroSerieCotas/v1']['get'];check('newAPI protected',op['security']==[{'Authorization':[]}] and api['components']['securitySchemes']['Authorization']['scheme']=='bearer')
dump('new-api-contract-excerpt.json',{'operation':op,'security_scheme':api['components']['securitySchemes']['Authorization'],'data_query_executed':False,'authentication_attempted':False})
dump('source-manifest.json',manifest);dump('request-results.json',requests);dump('coverage-summary.json',summary);csvsave('raw-versus-consistent-daily.csv',comparisons)
reused=['outputs/historico-cheias-mucum/documentation/ana-hidrowebservice-manual-2026.pdf','outputs/historico-cheias-mucum/documentation/ana-hidrowebservice-manual-2026.txt','outputs/pesquisa-diversidade-eventos-pre2020-20260922/README.md','outputs/pesquisa-diversidade-eventos-pre2020-20260922/artifact-hashes.json','outputs/historico-cheias-mucum/documentation/reference-investigation-report.md']
dump('reused-source-hashes.json',[{'file':x,'sha256':sha(R/x)} for x in reused])
dump('verification.json',{'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':all(x['passed'] for x in checks),'checks_count':len(checks),'checks':checks,'data_gets':12,'documentation_gets':6,'returned_monthly_records':len(records),'day_fields_inventoried':len(cells),'nonnull_day_fields':357,'candidate_window_cells':84,'raw_instant_candidate_readings':42,'old_hidro12_consistency_mapping_does_not_match_legacy_api':True,'daily_vs_instant_not_merged':True,'all_times_naive_preserved':True,'fit_inference_or_interpolation':False})
print('PASS',len(checks),'checks;',len(records),'monthly records;',len(cells),'day fields;357present;42rawinstantcandidate')
