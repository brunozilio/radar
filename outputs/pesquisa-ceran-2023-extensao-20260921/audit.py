from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter
import json,csv,calendar,math,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];IDS={'JIUHQJ':'14 DE JULHO','JIUHMC':'MONTE CLARO','JIUHCA':'CASTRO ALVES'};man=json.loads((P/'source-manifest.json').read_text());summary=[];selected=[];flags=[];gaps=[];inventory=[]
def save(name,rows):
 if rows:
  with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def n(v):
 try:return float(v)
 except (ValueError,TypeError):return float('nan')
for src in man:
 f=P/src['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==src['sha256'];month=int(f.stem[-2:]);start=datetime(2023,month,1);expected={start+timedelta(hours=h) for h in range(1,24*calendar.monthrange(2023,month)[1]+1)}
 with f.open() as fh:
  reader=csv.DictReader(fh,delimiter=';');rows=[];inv=Counter()
  for line,r in enumerate(reader,2):
   inv[r['id_reservatorio'],r['nom_reservatorio'],r['cod_usina']]+=1
   if r['id_reservatorio'] in IDS:rows.append({**r,'source_file':src['file'],'source_line':line})
 inventory.extend({'month':month,'id':a,'name':b,'code':c,'rows':nn} for (a,b,c),nn in inv.items());selected+=rows
 for rid,name in IDS.items():
  group=[r for r in rows if r['id_reservatorio']==rid];times=[datetime.fromisoformat(r['din_instante']) for r in group];et=[t+timedelta(minutes=1) if (t.hour,t.minute)==(23,59) else t for t in times];miss=sorted(expected-set(et));vv={}
  for col in [k for k in group[0] if k.startswith('val_')]:
   values=[n(r[col]) for r in group];good=[v for v in values if math.isfinite(v)];mx=max(good) if good else None
   vv[col]={'present':len(good),'missing':len(values)-len(good),'zeros':sum(v==0 for v in values),'negative':sum(v<0 for v in good),'count9999':sum(v==9999 for v in good),'min':min(good) if good else None,'max':mx,'max_at':[r['din_instante'] for r,v in zip(group,values) if v==mx]}
  reservoir_flags=[]
  for r in group:
   q=n(r['val_vazaodefluente']);comps=[n(r[c]) for c in ['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']];res=q-sum(comps);codes=[]
   if q==0 and all(math.isfinite(c) for c in comps) and sum(comps)>0:codes.append('ZERO_Q_POSITIVE_COMPONENTS')
   if math.isfinite(res) and abs(res)>1:codes.append('RESIDUAL_GT1_REVIEW_NOT_OFFICIAL_QC')
   if codes:reservoir_flags.append({**r,'diagnostic_flags':'|'.join(codes),'residual_m3_s':res})
  flags+=reservoir_flags;gaps.extend({'month':month,'id':rid,'missing_hour_end_interpreted':str(t)} for t in miss)
  summary.append({'month':month,'id':rid,'name':name,'observed_names':sorted({r['nom_reservatorio'] for r in group}),'codes':sorted({r['cod_usina'] for r in group}),'rows':len(group),'expected_hours':len(expected),'missing_rows':len(miss),'duplicates':len(times)-len(set(times)),'records2359':sum((t.hour,t.minute)==(23,59) for t in times),'variables':vv,'semantic_flag_rows':len(reservoir_flags)})
save('ceran-source-values.csv',selected);save('semantic-review.csv',flags);save('missing-hours.csv',gaps);save('reservoir-inventory.csv',inventory)
result={'created_at':datetime.now(timezone.utc).isoformat(),'months_verified':[1,6],'source_count':2,'summary':summary,'source_rows_selected':len(selected),'no_interpolation':True,'no_training':True,'no_new_holdout_claim':True,'time_assumption':'Hour-end according ONS catalog;23:59->24:00 only for gap inventory. Original string unchanged. Historical exporter timezone not proven; Brasilia assumed based on later ONS routine.'};(P/'catalog.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
for s in summary:print(s['month'],s['name'],'rows/gaps',s['rows'],s['missing_rows'],'Q/I/U/D',[(s['variables'][v]['present'],s['variables'][v]['zeros'],s['variables'][v]['max']) for v in ['val_vazaodefluente','val_vazaoafluente','val_nivelmontante','val_niveljusante']],'flags',s['semantic_flag_rows'])
