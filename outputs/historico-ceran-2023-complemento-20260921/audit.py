from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter
import json,csv,calendar,math,hashlib
ROOT=Path('/Users/brunozilio/Documents/radar');P=ROOT/'outputs/historico-ceran-2023-complemento-20260921'
IDS={'JIUHCA':'CASTRO ALVES','JIUHMC':'MONTE CLARO','JIUHQJ':'14 DE JULHO'}
CORE=['val_vazaodefluente','val_vazaoafluente','val_nivelmontante','val_niveljusante']
COMP=['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']
def n(v):
 try:return float(v)
 except (ValueError,TypeError):return float('nan')
def save(name,rows,fields=None):
 with (P/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def interpreted(s):
 d=datetime.fromisoformat(s)
 return d+timedelta(minutes=1) if (d.hour,d.minute,d.second)==(23,59,0) else d
def segments(t):
 out=[]
 for x in sorted(t):
  if out and x==out[-1][-1]+timedelta(hours=1):out[-1].append(x)
  else:out.append([x])
 return out
manifest=json.loads((P/'source-manifest.json').read_text())
selected=[];summaries=[];gaps=[];dups=[];flags=[];jumps=[];inventory=[];allmaps={rid:{} for rid in IDS};alltimes=set()
for src in manifest:
 if src.get('status')!=200:continue
 f=P/src['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==src['sha256']
 month=int(f.stem[-2:]);start=datetime(2023,month,1);expected={start+timedelta(hours=h) for h in range(1,24*calendar.monthrange(2023,month)[1]+1)};alltimes|=expected
 rows=[];inv=Counter()
 with f.open(encoding='utf-8-sig') as fh:
  for line,r in enumerate(csv.DictReader(fh,delimiter=';'),2):
   inv[r['id_reservatorio'],r['nom_reservatorio'],r['cod_usina']]+=1
   if r['id_reservatorio'] in IDS:
    r={**r,'source_file':src['file'],'source_line':line,'hour_end_interpreted_assumed':interpreted(r['din_instante']).isoformat(),'source_month':month}
    rows.append(r)
 selected+=rows
 inventory.extend({'month':month,'id':a,'name':b,'code':c,'rows':nn} for (a,b,c),nn in inv.items())
 for rid,name in IDS.items():
  group=[r for r in rows if r['id_reservatorio']==rid];counts=Counter(r['din_instante'] for r in group)
  du=[r for r in group if counts[r['din_instante']]>1];dups+=du
  et=[interpreted(r['din_instante']) for r in group];miss=sorted(expected-set(et))
  gaps.extend({'month':month,'id':rid,'missing_hour_end_interpreted':x.isoformat()} for x in miss)
  vals={}
  for col in [k for k in group[0] if k.startswith('val_')]:
   vv=[n(r[col]) for r in group];good=[v for v in vv if math.isfinite(v)]
   vals[col]={'finite':len(good),'nonfinite':len(vv)-len(good),'zeros':sum(v==0 for v in vv),'negative':sum(v<0 for v in good),'equals9999':sum(v==9999 for v in good),'min':min(good) if good else None,'max':max(good) if good else None}
   ordered=sorted(group,key=lambda r:interpreted(r['din_instante']));cand=[]
   for left,right in zip(ordered,ordered[1:]):
    if interpreted(right['din_instante'])-interpreted(left['din_instante'])!=timedelta(hours=1):continue
    v0,v1=n(left[col]),n(right[col])
    if math.isfinite(v0) and math.isfinite(v1):cand.append({'month':month,'id':rid,'variable':col,'from_time_original':left['din_instante'],'to_time_original':right['din_instante'],'from_value':v0,'to_value':v1,'difference':v1-v0,'source_file':right['source_file'],'from_line':left['source_line'],'to_line':right['source_line']})
   jumps.extend(sorted(cand,key=lambda r:abs(r['difference']),reverse=True)[:5])
  flagcount=0
  for r in group:
   q=n(r['val_vazaodefluente']);cc=[n(r[k]) for k in COMP];complete=all(math.isfinite(v) for v in cc)
   codes=[]
   if not complete:codes.append('COMPONENT_SUM_UNKNOWN')
   if q==0 and complete and sum(cc)>1:codes.append('ZERO_DEFLUENT_COMPONENT_SUM_GT1')
   if math.isfinite(q) and complete and abs(q-sum(cc))>1:codes.append('COMPONENT_RESIDUAL_ABS_GT1')
   for col in CORE+COMP:
    v=n(r[col])
    if not math.isfinite(v):codes.append('NONFINITE:'+col)
    elif v<0:codes.append('NEGATIVE:'+col)
    elif v==9999:codes.append('VALUE9999_UNINTERPRETED:'+col)
   if codes:
    flags.append({**r,'diagnostic_flags':'|'.join(codes),'component_sum':sum(cc) if complete else None,'component_residual':q-sum(cc) if complete and math.isfinite(q) else None});flagcount+=1
   at=interpreted(r['din_instante'])
   allmaps[rid].setdefault(at,[]).append(r)
  peaks={}
  for col in CORE:
   finite=[r for r in group if math.isfinite(n(r[col]))]
   peaks[col]=[{ 'time_original':r['din_instante'],'value':n(r[col]),'source_file':r['source_file'],'source_line':r['source_line']} for r in sorted(finite,key=lambda r:n(r[col]),reverse=True)[:5]]
  summaries.append({'month':month,'id':rid,'name':name,'observed_names':sorted({r['nom_reservatorio'] for r in group}),'codes':sorted({r['cod_usina'] for r in group}),'rows':len(group),'expected_hours':len(expected),'missing_hours':len(miss),'duplicate_rows_beyond_first':sum(c-1 for c in counts.values()),'duplicate_normalized_hours':len(et)-len(set(et)),'off_expected_grid_records':sum(x not in expected for x in et),'records2359':sum('23:59' in r['din_instante'] for r in group),'variables':vals,'top5_peaks':peaks,'flag_rows':flagcount})
save('ceran-source-values.csv',selected)
save('missing-hours.csv',gaps,['month','id','missing_hour_end_interpreted'])
save('duplicate-source-rows.csv',dups,list(selected[0]))
save('semantic-review.csv',flags,list(selected[0])+['diagnostic_flags','component_sum','component_residual'])
save('largest-hourly-jumps.csv',jumps)
save('reservoir-inventory.csv',inventory)
windows=[]
for label,cols in [('QI',CORE[:2]),('QI_levels',CORE)]:
 complete=[]
 for at in sorted(alltimes):
  if all(len(allmaps[rid].get(at,[]))==1 and all(math.isfinite(n(allmaps[rid][at][0][col])) for col in cols) for rid in IDS):complete.append(at)
 for seq in segments(complete):
  windows.append({'variables':label,'start_hour_end_interpreted':seq[0].isoformat(),'end_hour_end_interpreted':seq[-1].isoformat(),'hours':len(seq),'all_three_plants':True,'at_least_37h':len(seq)>=37,'potential_origin_start_with_24h_history_12h_future':(seq[0]+timedelta(hours=24)).isoformat() if len(seq)>=37 else None,'potential_origin_end_with_24h_history_12h_future':(seq[-1]-timedelta(hours=12)).isoformat() if len(seq)>=37 else None})
save('complete-windows.csv',windows)
peakwindows=[]
for s in summaries:
 peak=s['top5_peaks']['val_vazaodefluente'][0];center=interpreted(peak['time_original']);ts=[center+timedelta(hours=k) for k in range(-36,37)]
 counts={}
 for rid in IDS:
  counts[rid]={col:sum(len(allmaps[rid].get(at,[]))==1 and math.isfinite(n(allmaps[rid][at][0][col])) for at in ts) for col in CORE}
 peakwindows.append({'month':s['month'],'peak_plant':s['id'],'peak_q_m3_s':peak['value'],'peak_original_timestamp':peak['time_original'],'window_start':ts[0].isoformat(),'window_end':ts[-1].isoformat(),'expected_hours':73,'finite_unique_hours_by_plant_field':counts,'all_three_QI_complete':all(v[col]==73 for v in counts.values() for col in CORE[:2]),'all_three_QI_levels_complete':all(v[col]==73 for v in counts.values() for col in CORE)})
(P/'peak-window-coverage.json').write_text(json.dumps(peakwindows,indent=2)+'\n')
result={'created_at_utc':datetime.now(timezone.utc).isoformat(),'selected_rows':len(selected),'months':[2,3,4,5,7,8],'summary':summaries,'time_contract':'Original timestamp preserved. 23:59->24:00 ONLY for hour-end coverage hypothesis; timezone/datum not newly certified.','qc_contract':'Diagnostic only, no masks. Component sum unknown unless all three finite. Threshold abs residual>1 m3/s; no 9999 meaning inferred.','interpolation':False,'training':False,'semantic_flag_counts':dict(Counter(c for r in flags for c in r['diagnostic_flags'].split('|')))}
(P/'catalog.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
for s in summaries:print(s['month'],s['id'],s['rows'],'gaps',s['missing_hours'],'Q/I/U/D',[s['variables'][c]['finite'] for c in CORE],'Qmax',s['variables'][CORE[0]]['max'],'flags',s['flag_rows'])
print('Total',len(selected),'flags',result['semantic_flag_counts'])

