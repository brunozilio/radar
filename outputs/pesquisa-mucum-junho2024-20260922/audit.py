from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter,defaultdict
import json,hashlib,math,xml.etree.ElementTree as ET,csv
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(ROOT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
xml=ROOT/'raw/ana-86510000-20240615-20240621.xml'
receipt=json.loads(Path(str(xml)+'.receipt.json').read_text()); assert receipt['http_status']==200 and receipt['sha256']==sha(xml)
raw=[]
for e in ET.parse(xml).getroot().iter():
 if e.tag.split('}')[-1]=='DadosHidrometereologicos':raw.append({x.tag.split('}')[-1]:x.text for x in e})
records=[dict(r,source_file=str(xml.relative_to(REPO)),source_sha256=sha(xml),source_record_index=i+1) for i,r in enumerate(raw)]
records.sort(key=lambda r:(r['DataHora'],r['source_record_index']))
(ROOT/'ana-86510000-all-qc.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
assert all({k:v for k,v in r.items() if k not in ('source_file','source_sha256','source_record_index')}==raw[r['source_record_index']-1] for r in records)
bytime=defaultdict(list)
for r in records:bytime[r['DataHora']].append(r)
dups={t:rs for t,rs in bytime.items() if len(rs)>1}
conflicts={t:rs for t,rs in dups.items() if len({json.dumps(raw[r['source_record_index']-1],sort_keys=True) for r in rs})>1}
save('duplicates-conflicts.json',{'duplicate_timestamps':dups,'conflicts':conflicts})
start=datetime(2024,6,15);end=datetime(2024,6,22)
times=[datetime.fromisoformat(r['DataHora']) for r in records]
expected=[start+timedelta(minutes=15*i) for i in range(7*96)]
missing=[t.isoformat(' ') for t in expected if t not in set(times)]
fields={}
def num(x):
 try:return float(x)
 except (TypeError,ValueError):return float('nan')
for field in ('NivelFinal','NivelSensor','NivelManual','NivelDisplay','ChuvaFinal','ChuvaAcumAdotada','VazaoFinal'):
 vals=[num(r.get(field)) for r in records];good=[(r,v) for r,v in zip(records,vals) if math.isfinite(v)]
 approved=[(r,v) for r,v in good if r.get('CQ_'+field)=='Dado aprovado']
 fields[field]={'field_present':sum(field in r for r in records),'null_or_nonfinite':len(records)-len(good),'negative':sum(v<0 for r,v in good),'zero':sum(v==0 for r,v in good),'finite':len(good),'qc':dict(Counter(r.get('CQ_'+field) or '<empty>' for r in records)),'finite_approved':len(approved),'approved_min':min((v for r,v in approved),default=None),'approved_max':max((v for r,v in approved),default=None),'approved_max_times':[r['DataHora'] for r,v in approved if v==max((v for r,v in approved),default=None)]}
levels={datetime.fromisoformat(r['DataHora']):num(r.get('NivelFinal')) for r in records if r.get('CQ_NivelFinal')=='Dado aprovado' and math.isfinite(num(r.get('NivelFinal')))}
points=[]
for t,v in [('2024-06-17 22:00:00',1590.),('2024-06-20 07:00:00',879.)]:
 a=levels.get(datetime.fromisoformat(t));points.append({'timestamp_literal':t,'bulletin_cm':v,'ana_cm':a,'exact_agreement':a==v})
origins=[start+timedelta(hours=i) for i in range(168)]
coverage=[]
for h in range(1,13):
 pairs=[];boundary=missingbase=missingtarget=high=0
 for o in origins:
  t=o+timedelta(hours=h)
  if t>=end:boundary+=1;continue
  q=o-timedelta(minutes=15)
  options=[s for s in levels if s<=q]
  a=max(options) if options else None
  base=levels[a] if a is not None and q-a<=timedelta(minutes=15) else None
  target=levels.get(t)
  missingbase+=base is None;missingtarget+=target is None
  if base is not None and target is not None:pairs.append(o.isoformat(' '));high+=target>=700
 coverage.append({'horizon_h':h,'origins':168,'within_window_targets':168-boundary,'boundary_excluded':boundary,'missing_base':missingbase,'missing_exact_target':missingtarget,'valid_pairs':len(pairs),'valid_pairs_target_ge7m':high})
summary={'generated_utc':datetime.now(timezone.utc).isoformat(),'station_counts':dict(Counter(r['CodEstacao'] for r in records)),'records':len(records),'first_literal':min(times).isoformat(' '),'last_literal':max(times).isoformat(' '),'cadence_seconds':dict(Counter(str(int((b-a).total_seconds())) for a,b in zip(times,times[1:]))),'expected_quarter_hour_rows':672,'missing_expected_timestamps':missing,'exact_hour_rows':sum(t.minute==0 and t.second==0 for t in times),'duplicates':len(dups),'conflicts':len(conflicts),'fields':fields,'bulletin_comparison':points,'anchor_target_coverage':coverage,'units':{'NivelFinal':'cm (bulletin corroboration; original XML has no inline unit)','rain':'not independently unit-verified here','VazaoFinal':'not independently unit-verified here'},'timezone':'literal timezone-naive timestamps; UTC-03 assumption not certified by legacy endpoint contract','historical_publication':'unknown; current retrieval can include later QC/revisions','max_not_certified_continuous_peak':True,'no_inference_training_or_operational_change':True}
save('summary.json',summary)
with (ROOT/'anchor-target-coverage.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=coverage[0]);w.writeheader();w.writerows(coverage)
checks={'xml_records_roundtrip_exact':len(records),'source_hash_ok':receipt['sha256']==sha(xml),'all_station_expected':all(r['CodEstacao']=='86510000' for r in records),'complete_quarter_grid':times==expected,'duplicates_absent':not dups,'conflicts_absent':not conflicts,'all_levels_finite_approved':fields['NivelFinal']['finite_approved']==672,'bulletin_points_agree':all(p['exact_agreement'] for p in points)}
save('verification.json',{'passed':all(v is True or isinstance(v,int) and v>0 for v in checks.values()),'checks':checks})
print(json.dumps(summary,ensure_ascii=False,indent=2))
