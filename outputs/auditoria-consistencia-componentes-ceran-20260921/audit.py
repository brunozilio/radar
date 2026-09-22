"""No mutations outside own output directory; diagnostic only, no source masks."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
import csv,json,math,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];RAW=ROOT/'outputs/mucum-propagacao-2026-09-21/raw';FILES=sorted(RAW.glob('DADOS_HIDROLOGICOS_HO_*-ceran.csv'));assert len(FILES)==18
FIELDS=['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas'];IDS={'JIUHQJ':'14 de Julho','JIUHMC':'Monte Claro','JIUHCA':'Castro Alves'};cut='2026-07-01 00:00:00';source=[];zero=[];flagged=[];unknown=[];focus=[];all_unknown=[];stats=defaultdict(Counter);seen=Counter();duplicates=[]
def num(x):
 try:v=float(x);return v if math.isfinite(v) else None
 except (ValueError,TypeError):return None
def save(name,rs,columns=None):
 with (P/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=columns or list(rs[0]) if rs else columns or ['empty']);w.writeheader();w.writerows(rs)
for f in FILES:
 h=hashlib.sha256(f.read_bytes()).hexdigest();source.append({'path':str(f.relative_to(ROOT)),'sha256':h,'bytes':f.stat().st_size})
 with f.open() as fh:
  for lineno,r in enumerate(csv.DictReader(fh,delimiter=';'),2):
   rid=r['id_reservatorio'].strip();assert rid in IDS;t=r['din_instante'];phase='before_2026_07_01' if t<cut else 'on_or_after_2026_07_01';s=stats[rid,phase];s['rows']+=1;key=rid,t;seen[key]+=1
   if seen[key]>1:duplicates.append({'id':rid,'at':t,'file':str(f.relative_to(ROOT)),'line':lineno})
   q=num(r['val_vazaodefluente']);comp=[num(r[k]) for k in FIELDS];complete=all(v is not None for v in comp);total=sum(comp) if complete else None
   if q is None:s['Q_missing_nonfinite']+=1
   if not complete:s['any_component_unknown_all_Q']+=1
   classification='NOT_ZERO_Q'
   if q==0:
    s['Q_zero']+=1
    if not complete:classification='ZERO_Q_COMPONENT_SUM_UNKNOWN';s['zero_Q_incomplete_components']+=1
    elif total>1:classification='ZERO_Q_COMPONENT_SUM_GT1_DIAGNOSTIC';s['flagged_complete_sum_gt1']+=1
    else:classification='ZERO_Q_COMPLETE_SUM_LE1';s['zero_Q_complete_sum_le1']+=1
   row={**r,'plant_name':IDS[rid],'phase':phase,'components_complete':complete,'component_sum_m3_s':total if total is not None else '', 'diagnostic_class':classification,'source_file':str(f.relative_to(ROOT)),'source_line':lineno,'source_sha256':h}
   if not complete:all_unknown.append(row)
   if q==0:
    zero.append(row)
    if classification=='ZERO_Q_COMPONENT_SUM_GT1_DIAGNOSTIC':flagged.append(row)
    elif not complete:unknown.append(row)
   if rid=='JIUHMC' and t.startswith('2026-07-22'):focus.append(row)
save('unknown-components-all-defluences.csv',all_unknown);save('zero-defluence-all.csv',zero);save('flagged-complete-components.csv',flagged);save('zero-with-unknown-components.csv',unknown);save('monte-claro-2026-07-22.csv',focus);save('duplicate-timestamps.csv',duplicates)
daily=Counter((r['id_reservatorio'].strip(),r['din_instante'][:10],r['phase']) for r in flagged);save('flagged-by-date.csv',[{'id':k[0],'plant':IDS[k[0]],'date':k[1],'phase':k[2],'flagged_rows':v} for k,v in sorted(daily.items())])
result={'audited_at':datetime.now(timezone.utc).isoformat(),'rule':'Qdef exactly0 AND Qtur,Qvert,Qoutras all finite AND their sum>1m3/s. Tolerance is diagnostic, not official QC. Missing component=>unknown total, never0.','units':'m3/s','split_original_timestamp':'2026-07-01 00:00:00; preserved ONS labels, Brasilia interpretation assumption','source_files':len(FILES),'source_rows':sum(v['rows'] for v in stats.values()),'duplicate_keys':len(duplicates),'counts':[{'id':rid,'plant':IDS[rid],'phase':phase,**{k:c[k] for k in ['rows','Q_missing_nonfinite','Q_zero','any_component_unknown_all_Q','zero_Q_incomplete_components','flagged_complete_sum_gt1','zero_Q_complete_sum_le1']}} for (rid,phase),c in sorted(stats.items())],'flagged_rows':len(flagged),'flagged_days':len(daily),'zero_Q_unknown_components':len(unknown),'monte_july22':{'rows':len(focus),'zero_Q':sum(num(r['val_vazaodefluente'])==0 for r in focus),'flagged':sum(r['diagnostic_class']=='ZERO_Q_COMPONENT_SUM_GT1_DIAGNOSTIC' for r in focus),'unknown':sum(r['diagnostic_class']=='ZERO_Q_COMPONENT_SUM_UNKNOWN' for r in focus)},'all_zero_rows_partition_check':len(zero)==len(flagged)+len(unknown)+sum(r['diagnostic_class']=='ZERO_Q_COMPLETE_SUM_LE1' for r in zero),'no_model_training':True,'source_changes':False,'official_invalidity_claim':False}
(P/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(P/'source-manifest.json').write_text(json.dumps(source,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
print('DATES',sorted(daily.items()))
