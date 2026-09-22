"""Read-only source audit; writes exclusively inside its own output directory."""
from pathlib import Path
import csv,json,hashlib,math,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21';RAW=ROOT/'outputs/mucum-propagacao-2026-09-21/raw';EXP=ROOT/'outputs/experimento-niveis-ate-mucum-pesos-zero-20260921'
TZ=timezone(timedelta(hours=-3));epoch=lambda s:datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp();iso=lambda t:datetime.fromtimestamp(float(t),TZ).isoformat()
inputs={}
def add(p):inputs[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def dump(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(n,rows):
 if rows:
  with (OUT/n).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def number(v):
 try:return float(v) if math.isfinite(float(v)) and float(v)>=0 else float('nan')
 except (ValueError,TypeError):return float('nan')
def val(r,k):return number(r.get(k)) if r.get('CQ_'+k) in ('Dado aprovado',None) else float('nan')
records={};rawsummary=[];variants=defaultdict(list)
for p in sorted((ROOT/'outputs').glob('*/raw/ana-86500000*.xml')):
 add(p);text=p.read_text();lines={};start=0
 for i,line in enumerate(text.splitlines(),1):
  if '<DadosHidrometereologicos ' in line:start=i
  m=re.search(r'<DataHora>(.*?)</DataHora>',line)
  if m:lines[m[1]]=start
 rows={};dups=0
 for el in ET.fromstring(text).iter():
  if el.tag.split('}')[-1]!='DadosHidrometereologicos':continue
  r={x.tag.split('}')[-1]:x.text for x in el};at=epoch(r['DataHora']);dups+=at in rows;r['_path']=str(p.relative_to(ROOT));r['_line']=lines[r['DataHora']];rows[at]=r;variants[at].append(r)
 records[p]=rows;rawsummary.append({'path':str(p.relative_to(ROOT)),'rows':len(rows),'duplicates':dups,'start':iso(min(rows)) if rows else None,'end':iso(max(rows)) if rows else None,'q_qc_counts':dict(Counter(str(r.get('CQ_VazaoFinal')) for r in rows.values())),'q_empty':sum(r.get('VazaoFinal') is None for r in rows.values())})
# Reproduce the current historical parser without calling it (which could rewrite its cache).
sources=[RAW/'ana-86500000-2025.xml',RAW/'ana-86500000.xml',RAW/'ana-86500000-latest.xml'];merged={};effective={}
for p in sources:
 for t,r in records[p].items():
  arr=merged.setdefault(t,[float('nan')]*2)
  for j,k in enumerate(['NivelFinal','VazaoFinal']):
   v=val(r,k)/(100 if j==0 else 1)
   if math.isfinite(v):arr[j]=v
  effective[t]=r
cachep=RAW/'normalized-86500000.npz';add(cachep);cache=dict(np.load(cachep));cachemap={float(t):(float(h),float(q)) for t,h,q in zip(cache['times'],cache['level'],cache['flow'])}
cache_diff=[{'at':iso(t),'parsed_h':None if not math.isfinite(v[0]) else v[0],'parsed_q':None if not math.isfinite(v[1]) else v[1]} for t,v in merged.items() if t not in cachemap or not np.allclose(v,cachemap[t],equal_nan=True)]
fresh=BASE/'raw/ana-86500000-fresh.xml'
for t,r in records[fresh].items():merged[t]=[val(r,'NivelFinal')/100,val(r,'VazaoFinal')];effective[t]=r
zp=BASE/'telemetria-latencia.npz';dp=BASE/'dados-roteamento.npz';add(zp);add(dp);z=dict(np.load(zp));d=dict(np.load(dp));t=z['times'];frozenq=z['raw:86500000:Q'];frozenh=z['raw:86500000:H'];parsed=np.array([merged.get(float(at),[float('nan')]*2) for at in t]);frozen_diff=np.where(~np.isclose(parsed[:,1],frozenq,equal_nan=True))[0]
cut=epoch('2026-09-21T00:00:00');test=epoch('2026-07-01T00:00:00');prefix=test-25*3600
missing=[]
for i in np.where(~np.isfinite(frozenq))[0]:
 at=float(t[i]);r=effective.get(at);cls='no_exact_record' if r is None else 'q_empty' if r.get('VazaoFinal') is None else 'q_qc_rejected' if r.get('CQ_VazaoFinal') not in ('Dado aprovado',None) else 'q_number_rejected'
 missing.append({'at':iso(at),'epoch':at,'scope':'evaluation' if test<=at<cut else 'prefix' if prefix<=at<test else 'other','classification':cls,'level_approved_m':float(frozenh[i]) if np.isfinite(frozenh[i]) else '', 'raw_level_cm':r.get('NivelFinal') if r else '', 'raw_level_qc':r.get('CQ_NivelFinal') if r else '', 'raw_flow':r.get('VazaoFinal') if r else '', 'raw_flow_qc':r.get('CQ_VazaoFinal') if r else '', 'source_path':r['_path'] if r else '', 'record_start_line':r['_line'] if r else '', 'approved_q_in_other_preserved_xml':sum(math.isfinite(val(v,'VazaoFinal')) for v in variants[at])})
save('missing-quarter-hours.csv',missing)
intervals=[]
for scope,lo,hi in [('full',t[0],t[-1]+900),('evaluation',test,cut),('evaluation_with_prefix',prefix,cut)]:
 ix=np.where((t>=lo)&(t<hi)&~np.isfinite(frozenq))[0]
 for g in np.split(ix,np.where(np.diff(ix)>1)[0]+1):
  if not len(g):continue
  rr=[r for r in missing if t[g[0]]<=r['epoch']<=t[g[-1]]]
  intervals.append({'scope':scope,'start':iso(t[g[0]]),'end_inclusive':iso(t[g[-1]]),'quarter_hours':len(g),'with_approved_level':int(np.isfinite(frozenh[g]).sum()),'classes':json.dumps(dict(Counter(r['classification'] for r in rr)))})
save('missing-intervals.csv',intervals)
# Enumerate actual missing input timestamps responsible for the failed pairs.
failp=EXP/'failure-causes.csv';add(failp);add(EXP/'failure-causes.json');fail=list(csv.DictReader(failp.open()));weights=list(csv.DictReader((BASE/'roteamento-vazao-pesos.csv').open()));add(BASE/'roteamento-vazao-pesos.csv');lags=[int(r['lag_h']) for r in weights if r['source']=='Passo Carreiro' and float(r['weight'])!=0];dt=d['times'];q=d['carreiro'];known=z['86500000:Q'][np.searchsorted(t,dt)];deps=defaultdict(lambda:{'pairs':set(),'reasons':set(),'origins':set()})
for rowno,r in enumerate(fail):
 at=epoch(r['origin']);i=int(np.searchsorted(dt,at));h=int(r['nominal_lead_h']);rel=[]
 for lag in lags:
  for hh in [-1,0]:
   j=i+hh-lag
   if not np.isfinite(q[j]):rel.append((dt[j],'anchor_history_missing'))
  k=h-lag
  if k<0 and not np.isfinite(q[i+k]):rel.append((dt[i+k],'forecast_history_missing'))
 if h>=min(lags) and not np.isfinite(known[i]):rel.append((at-1800,'known_base_missing'))
 for source_time,reason in set(rel):
  dep=deps[source_time];dep['pairs'].add(rowno);dep['reasons'].add(reason);dep['origins'].add(at)
mm={r['epoch']:r for r in missing};deprows=[]
for at,x in sorted(deps.items()):
 r=mm.get(at,{})
 deprows.append({'source_at':iso(at),'affected_target_pairs':len(x['pairs']),'affected_origins':len(x['origins']),'reasons':'|'.join(sorted(x['reasons'])),'classification':r.get('classification','investigate_asof_neighbor'),'level_approved_m':r.get('level_approved_m',''),'source_path':r.get('source_path',''),'record_start_line':r.get('record_start_line','')})
save('missing-input-dependencies.csv',deprows)
versiondiff=[]
for at,vs in sorted(variants.items()):
 unique={(v.get('NivelFinal'),v.get('CQ_NivelFinal'),v.get('VazaoFinal'),v.get('CQ_VazaoFinal')) for v in vs}
 if len(unique)>1:
  for r in vs:versiondiff.append({'at':iso(at),'path':r['_path'],'record_start_line':r['_line'],**{k:r.get(k) for k in ['NivelFinal','CQ_NivelFinal','VazaoFinal','CQ_VazaoFinal']}})
save('xml-version-differences.csv',versiondiff)
# Compare later normalized archives at the exact frozen missing timestamps (without adopting them).
later=[]
for p in sorted((ROOT/'outputs').glob('*/history/ana-86500000.npz')):
 add(p);a=dict(np.load(p));lookup={float(at):float(v) for at,v in zip(a['times'],a['flow'])};recovered=[r['at'] for r in missing if math.isfinite(lookup.get(r['epoch'],float('nan')))];later.append({'path':str(p.relative_to(ROOT)),'start':iso(a['times'][0]),'end':iso(a['times'][-1]),'frozen_missing_q_now_finite':len(recovered),'recovered_times':recovered})
for p in [ROOT/'scripts/hydro_routing_data.py',ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_model.py']:add(p)
summary={'audited_at':datetime.now(TZ).isoformat(),'timezone':'UTC-03 assumed consistently with frozen parser; no new historical contract verification','units':{'raw_level':'cm','normalized_level':'m','flow':'m3/s'},'no_imputation':True,'source_xml':rawsummary,'cache_reproduction_differences':len(cache_diff),'frozen_raw_q_reproduction_differences':len(frozen_diff),'xml_version_difference_timestamps':len(set(r['at'] for r in versiondiff)),'missing_quarter_hours':{},'failure_pairs':len(fail),'failed_origins':len(set(r['origin'] for r in fail)),'distinct_missing_dependencies':len(deps),'failure_pairs_explained_by_dependencies':len(set().union(*(v['pairs'] for v in deps.values()))),'dependency_classes':dict(Counter(r['classification'] for r in deprows)),'later_normalized_archives':later,'input_manifest':inputs}
for name,lo,hi in [('full',t[0],t[-1]+900),('evaluation',test,cut),('evaluation_with_prefix',prefix,cut)]:
 rr=[r for r in missing if lo<=r['epoch']<hi];summary['missing_quarter_hours'][name]={'total':len(rr),'with_approved_level':sum(r['level_approved_m']!='' for r in rr),'with_any_numeric_raw_level':sum(math.isfinite(number(r['raw_level_cm'])) for r in rr),'classes':dict(Counter(r['classification'] for r in rr)),'approved_q_other_version':sum(r['approved_q_in_other_preserved_xml']>0 for r in rr)}
dump('summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ['input_manifest','source_xml','later_normalized_archives']},ensure_ascii=False,indent=2));print('later recovery',[(r['path'],r['frozen_missing_q_now_finite']) for r in later])
