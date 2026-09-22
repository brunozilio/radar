"""Independent strict-QC rain interval audit; no matrix builder/helper imports."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib,datetime as dt,math
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];A=W/'outputs/radar-insumos-observados-2018-20260922'
paths={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):paths[str(p.relative_to(W))]=sha(p);return p
def read(p):return json.loads(use(p).read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(name,rows):
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def parse(r):
 try:v=float(r.get('ChuvaFinal'))
 except (ValueError,TypeError):return np.nan
 return v if math.isfinite(v) and 0<=v<=150 and r.get('CQ_ChuvaFinal')=='Dado aprovado' else np.nan
def ended_overlap(left,right,amount,duration,queries,hours):
 p=[];c=[]
 for q in queries:
  keep=(right<=q)&(right>q-hours*3600);length=right[keep]-np.maximum(left[keep],q-hours*3600)
  p.append(float(np.sum(length/duration[keep]*amount[keep])));c.append(float(np.clip(np.sum(length)/(hours*3600),0,1)))
 return np.array(p),np.array(c)
def main():
 manifest=read(A/'manifest.json')
 for item in manifest['files']:assert sha(A/item['file'])==item['sha256']
 weights=read(W/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json');lags=read(W/'outputs/auditoria-latencias-chuva-20260921/latencies.json')['stations'];plan=read(A/'plan.json')
 assert len(lags)==27 and {r['station'] for r in lags}==set(plan['stations'])
 for p in ['scripts/hydro_rain_windows.py','scripts/hydro_latency_forecast.py']:use(W/p)
 stats=[];exceptions=[];regional=[];windows=[]
 reqs=[(h,0) for h in [1,3,6,12,24,48]]+[(3,h) for h in [3,6,12]]
 for win in plan['windows']:
  start=dt.datetime.fromisoformat(win['start']);origins=np.arange(3*86400,10*86400,3600,dtype=float);rain={}
  for lag in lags:
   code=lag['station'];p=use(A/'stations'/win['id']/f'ana-{code}-all-qc.jsonl');rows=[json.loads(l) for l in p.read_text().splitlines()]
   ts=np.array([(dt.datetime.fromisoformat(r['DataHora'])-start).total_seconds() for r in rows]);assert np.all(np.diff(ts)>0)
   duration=np.r_[0,np.diff(ts)] if len(ts) else np.array([]);v=np.array([parse(r) for r in rows]);good=np.isfinite(v)&(duration>0)&(duration<=5400)
   steps=int(lag['delay_seconds']/900);assert steps==lag['shift_steps_15min'];delay=steps*900
   stats.append({'window':win['id'],'station':code,'raw_records':len(rows),'strict_qc_range_finite':int(np.isfinite(v).sum()),'admissible_intervals':int(good.sum()),'first_record_no_interval':int(len(rows)>0),'intervals_over90min':int((duration>5400).sum()),'finite_rain_over90min':int(((duration>5400)&np.isfinite(v)).sum()),'admissible_duration_hours':float(duration[good].sum()/3600),'shift_steps_15min':steps,'effective_delay_seconds':delay,'original_delay_seconds':lag['delay_seconds'],'discarded_fraction_seconds':lag['delay_seconds']-delay,'cadence_counts_json':json.dumps(dict(Counter(int(x) for x in duration[1:]))),'off_quarter_records':sum(dt.datetime.fromisoformat(r['DataHora']).minute%15!=0 or dt.datetime.fromisoformat(r['DataHora']).second!=0 for r in rows)})
   for i,r in enumerate(rows):
    if duration[i]>5400 or (0<duration[i]<900) or (0<duration[i]<=5400 and duration[i]%900!=0) or not np.isfinite(v[i]):
     exceptions.append({'window':win['id'],'station':code,'timestamp_literal':r['DataHora'],'previous_timestamp_literal':rows[i-1]['DataHora'] if i else '', 'elapsed_seconds':float(duration[i]),'ChuvaFinal':r.get('ChuvaFinal'),'CQ_ChuvaFinal':r.get('CQ_ChuvaFinal'),'admissible':bool(good[i]),'source_file':r['source_file'],'source_record_index':r['source_record_index']})
   left=ts[good]-duration[good];right=ts[good];amount=v[good];dur=duration[good]
   for h,back in reqs:rain[code,h,back]=ended_overlap(left,right,amount,dur,origins-delay-back*3600,h)
  cols=[];names=[]
  for group in weights:
   values={}
   for h,back in reqs:
    amount=sum(w*rain[c,h,back][0] for c,w in group['weights'].items());coverage=sum(w*rain[c,h,back][1] for c,w in group['weights'].items());p=np.where(coverage>=.5,amount,np.nan);values[h,back]=(p,coverage)
    regional.append({'window':win['id'],'group':group['group'],'window_h':h,'back_h':back,'origins':len(origins),'finite_precipitation':int(np.isfinite(p).sum()),'coverage_min':float(coverage.min()),'coverage_max':float(coverage.max()),'coverage_mean':float(coverage.mean())})
   for h in [1,3,6,12,24,48]:cols.extend(values[h,0]);names.extend([group['group']+f':P{h}',group['group']+f':C{h}'])
   for back in [3,6,12]:cols.append(values[3,back][0]);names.append(group['group']+f':P3lag{back}')
  F=np.column_stack(cols);assert F.shape==(168,75)
  literal=np.array([(start+dt.timedelta(seconds=float(t))).isoformat(' ') for t in origins]);np.savez_compressed(R/f"rain-reconstructed-{win['id']}.npz",origin_literals=literal,rain_features=F,names=np.array(names))
  windows.append({'window':win['id'],'shape':list(F.shape),'finite':int(np.isfinite(F).sum()),'nan':int(np.isnan(F).sum())})
 save('rain-intervals-by-station.csv',stats);save('rain-exceptional-intervals.csv',exceptions);save('rain-regional-coverage-independent.csv',regional)
 dump(R/'rain-contract-verification.json',{'status':'Independent pre-matrix contract reconstruction; not yet a matrix comparison','windows':windows,'source_sha256':paths,'contract':{'strict_qc':'Dado aprovado','rain_range_mm':[0,150],'duration_seconds':'0<dt<=5400','availability':'interval end<=query; all timestamps retained when forming dt','regional_threshold':.5,'renormalize_weights':False,'delay':'int(frozen_delay_seconds/900)*900, whole measured windows shifted','partial_interval':'uniform proportional amount only where ended interval crosses left edge','timezone_datum_publication_certified':False},'known_limit':'Rain regional coverage is a feature-construction diagnostic, not prediction accuracy or historical publication verification.'})
 print('Independent rain reconstruction:',windows)
 print('86200900:',[r for r in stats if r['station']=='86200900'])
if __name__=='__main__':main()
