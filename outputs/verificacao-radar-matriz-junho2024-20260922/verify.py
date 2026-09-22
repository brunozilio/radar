"""Independent June2024 source-to-matrix audit; imports no production helpers/models."""
from pathlib import Path
import json,csv,hashlib,datetime as dt,math
import numpy as np
from rain_contract_audit import ended_overlap
R=Path(__file__).resolve().parent;W=R.parents[1];M=W/'outputs/radar-matriz-observada-junho2024-20260922';A=W/'outputs/radar-insumos-observados-junho2024-20260922';O=W/'outputs/auditoria-qi-radar-junho2024-20260922'
TZ=dt.timezone(dt.timedelta(hours=-3));checks=[];sources={}
LEVELS={'86510000':(900,900),'86472000':(1800,900),'86472600':(900,900),'86500000':(1800,900)}
PLANTS={'julho':'JIUHQJ','monte':'JIUHMC','castro':'JIUHCA'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(W))]=sha(p);return p
def read(p):return json.loads(use(p).read_text())
def csvread(p):return list(csv.DictReader(use(p).open()))
def ep(s):
 d=dt.datetime.fromisoformat(s);return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(t):return dt.datetime.fromtimestamp(t,TZ).isoformat()
def ck(name,b):assert b,name;checks.append({'check':name,'passed':True})
def compare(name,a,b,tol=0):
 a=np.asarray(a);b=np.asarray(b);ck(name+' shape',a.shape==b.shape);ck(name+' NaNs',np.array_equal(np.isnan(a),np.isnan(b)));np.testing.assert_allclose(a,b,atol=tol,rtol=0,equal_nan=True,err_msg=name)
 good=np.isfinite(a)&np.isfinite(b);checks.append({'check':name,'passed':True,'cells':int(a.size),'maximum_difference':float(np.max(np.abs(a[good]-b[good]))) if good.any() else 0,'tolerance':tol})
def number(x):
 try:v=float(x);return v if math.isfinite(v) else np.nan
 except (ValueError,TypeError):return np.nan
def parse(r,f):
 v=number(r.get(f));ok=np.isfinite(v) and v>=0 and r.get('CQ_'+f)=='Dado aprovado' and (f!='ChuvaFinal' or v<=150)
 return v/100 if ok and f=='NivelFinal' else (v if ok else np.nan)
def asof(t,v,q,age):
 out=np.full(len(q),np.nan);idx=np.searchsorted(t,q,side='right')-1
 if len(t):
  good=(idx>=0)&(q-t[np.maximum(idx,0)]<=age);out[good]=v[idx[good]]
 return out,idx
def back(a,n):return np.r_[np.full(n,np.nan),a[:-n]] if n else a.copy()
def manifest(folder,file):
 entries=read(folder/file);entries=entries['files'] if isinstance(entries,dict) else entries
 for r in entries:ck('hash '+str(folder.relative_to(W))+'/'+r['file'],sha(folder/r['file'])==r['sha256'])
def save(name,rows):
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 for d,f in [(A,'manifest.json'),(O,'artifact-hashes.json'),(M,'artifact-hashes.json')]:manifest(d,f)
 protocol=read(W/'docs/radar-june2024-observed-features-protocol.json');weights=read(W/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json');lags=read(W/'outputs/auditoria-latencias-chuva-20260921/latencies.json')['stations']
 ons=[]
 for ref in read(O/'ons-references.json'):
  p=use(W/ref['literal_csv']);raw=use(W/ref['raw_source_path']);ck('ONS '+ref['month'],sha(p)==ref['csv_sha256'] and sha(raw)==ref['raw_source_sha256']);ons.extend(csvread(p))
 storedlevels=csvread(M/'level-source-trace.csv');storedqi=csvread(O/'lag-source-trace.csv');storedtargets=csvread(M/'target-coverage.csv');storedrain=csvread(M/'rain-coverage.csv');storedfeatures=csvread(M/'feature-coverage.csv');catalog=read(M/'feature-catalog.json');results=[];targetaudit=[];levelaudit=[];featureaudit=[]
 for win in protocol['windows']:
  label=win['origin_start'];warm=win['warmup_start'];D=dict(np.load(use(M/f'{label}-features.npz')));Q=dict(np.load(use(M/f'{label}-quarter-hour.npz')))
  grid=np.arange(ep(warm),ep(win['stop_exclusive']),900);times=np.arange(ep(label),ep(win['stop_exclusive']),3600);idx=np.searchsorted(grid,times);compare(label+' grid',grid,Q['times']);compare(label+' origins',times,D['times']);ck(label+' 168x120',D['features'].shape==(168,120));ck(label+'960quarters',len(grid)==960)
  cols=[];names=[];cache={};delayed={}
  for code in sorted(r['station'] for r in lags):
   p=use(A/'stations'/f'ana-{code}-all-qc.jsonl');rows=[json.loads(l) for l in p.read_text().splitlines()];ts=np.array([ep(r['DataHora']) for r in rows]);ck(label+code+' chronological',np.all(np.diff(ts)>0));cache[code]=(rows,ts)
  for code,(lag,age) in LEVELS.items():
   rows,ts=cache[code];v=np.array([parse(r,'NivelFinal') for r in rows]);raw,_=asof(ts,v,grid,0);h,_=asof(ts,v,grid-lag,age);delayed[code]=h
   compare(label+code+' rawH',raw,Q['raw:'+code+':H']);compare(label+code+' delayedH',h,Q[code+':H']);cols.append(h[idx]);names.append(code+':H')
   for dh in [.5,1,2,4,8]:cols.append(((h-back(h,int(dh*4)))/dh)[idx]);names.append(code+f':dH{dh}')
   if code=='86510000':truth=raw[idx];base=h[idx];compare(label+' base',base,D['base']);compare(label+' truth',truth,D['truth'])
   _,ix=asof(ts,v,times-lag,age)
   for j,origin in enumerate(times):
    r=next(x for x in storedlevels if x['window']==label and x['station']==code and x['origin_assumed_brt']==iso(origin));k=ix[j];q=origin-lag;source=ts[k] if k>=0 else None;usable=bool(k>=0 and q-ts[k]<=age and np.isfinite(v[k]));ck('leveltrace '+label+code+str(j),r['query_assumed_brt']==iso(q) and r['source_assumed_brt']==(iso(source) if source is not None else '') and r['usable']==str(usable) and (float(r['age_seconds'])==q-source if source is not None else r['age_seconds']==''))
    ck('levelvalue '+label+code+str(j),number(r['value_m'])==v[k] if usable else r['value_m']=='');ck('level preorigin '+label+code+str(j),source is None or source<origin)
    if code=='86510000':levelaudit.append({'window':label,'origin':iso(origin),'anchor':iso(q),'selected':iso(source) if source is not None else '', 'raw_qc':rows[k].get('CQ_NivelFinal') if k>=0 else '', 'base':float(v[k]) if usable else None,'usable':usable})
  for plant,code in PLANTS.items():
   rows=sorted((r for r in ons if r['id_reservatorio'].strip()==code),key=lambda r:r['din_instante']);ts=np.array([ep(r['din_instante']) for r in rows]);ck(plant+' unique ONS',len(set(ts))==len(ts));pd={}
   for key,field in [('Q','val_vazaodefluente'),('I','val_vazaoafluente')]:
    v=np.array([number(r[field]) for r in rows]);raw,_=asof(ts,v,grid,5400);h,_=asof(ts,v,grid-3600,5400);pd[key]=h;compare(label+plant+key+' raw',raw,Q['raw:'+plant+':'+key]);compare(label+plant+key+' delayed',h,Q[plant+':'+key])
   q=pd['Q']/1000;power=np.maximum(q,0)**.6;cols.extend([power[idx],q[idx],pd['I'][idx]/1000]);names.extend([plant+':Q06',plant+':Q',plant+':I'])
   for dh in [1,2,4,8]:cols.append(((power-back(power,dh*4))/dh)[idx]);names.append(plant+f':dQ{dh}')
   for r in (r for r in storedqi if r['window']==label and r['plant']==code):
    origin=ep(r['origin_literal']);query=origin-(1+int(r['back_hours']))*3600;k=np.searchsorted(ts,query,side='right')-1;field='val_vazaodefluente' if r['variable']=='Q' else 'val_vazaoafluente';value=number(rows[k][field]) if k>=0 else np.nan;usable=bool(k>=0 and query-ts[k]<=5400 and np.isfinite(value));source=rows[k] if k>=0 else {}
    ck('QItrace '+str((label,code,r['origin_literal'],r['variable'],r['back_hours'])),ep(r['query_literal'])==query and r['source_literal']==source.get('din_instante','') and number(r['age_seconds'])==query-ts[k] and r['usable']==str(usable) and number(r['value_m3s'])==value and r['source_file']==source['source_file'] and r['source_record_index']==source['source_record_index'] and ts[k]<origin)
    comp=[number(source[f]) for f in ['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']];isq=r['variable']=='Q';ck('QIflags '+str((label,code,r['origin_literal'],r['variable'],r['back_hours'])),r['uses_zero']==str(bool(value==0)) and r['Q_zero_positive_components']==str(bool(isq and value==0 and np.isfinite(comp).all() and sum(comp)>1)) and r['Q_balance_residual_gt1']==str(bool(isq and np.isfinite(comp).all() and abs(value-sum(comp))>1)))
  compare(label+' first45',np.column_stack(cols),D['features'][:,:45]);rain={}
  for lag in lags:
   code=lag['station'];rows,ts=cache[code];v=np.array([parse(r,'ChuvaFinal') for r in rows]);duration=np.r_[0,np.diff(ts)] if len(ts) else np.array([]);good=np.isfinite(v)&(duration>0)&(duration<=5400);steps=int(lag['delay_seconds']/900);ck(label+code+' frozen truncation',steps==lag['shift_steps_15min'])
   for h in [1,3,6,12,24,48]:rain[code,h]=ended_overlap(ts[good]-duration[good],ts[good],v[good],duration[good],grid-steps*900,h)
  for group in weights:
   for h in [1,3,6,12,24,48]:
    p=sum(w*rain[c,h][0] for c,w in group['weights'].items());coverage=sum(w*rain[c,h][1] for c,w in group['weights'].items());value=np.where(coverage>=.5,p,np.nan);compare(label+group['group']+f' P{h} quarter',value,Q[group['group']+f':P{h}'],2e-10);compare(label+group['group']+f' C{h} quarter',coverage,Q[group['group']+f':C{h}'],2e-10);cols.extend([value[idx],coverage[idx]]);names.extend([group['group']+f':P{h}',group['group']+f':C{h}'])
    saved=next(r for r in storedrain if r['window']==label and r['group']==group['group'] and int(r['hours'])==h);ck(label+group['group']+f' coverage{h}',int(saved['finite_precipitation'])==np.isfinite(value[idx]).sum() and max(abs(float(saved[k])-v) for k,v in [('coverage_min',coverage[idx].min()),('coverage_max',coverage[idx].max()),('coverage_mean',coverage[idx].mean())])<2e-10)
    if h==3:p3=value
   for backh in [3,6,12]:cols.append(back(p3,backh*4)[idx]);names.append(group['group']+f':P3lag{backh}')
  F=np.column_stack(cols);compare(label+' all120',F,D['features'],2e-10);ck(label+' catalog',names==catalog);compare(label+' complete24',np.isfinite(F[:,:24]).all(1).astype(float),D['complete24'].astype(float));ck(label+' missing Linha and Carreiro',np.isnan(F[:,6:12]).all() and np.isnan(F[:,18:24]).all())
  for j in range(120):
   r=next(r for r in storedfeatures if r['window']==label and int(r['column'])==j);ck(label+'featurecoverage'+str(j),int(r['finite'])==np.isfinite(F[:,j]).sum() and int(r['missing'])==np.isnan(F[:,j]).sum());featureaudit.append({'window':label,'column':j,'name':names[j],'finite':int(np.isfinite(F[:,j]).sum()),'missing':int(np.isnan(F[:,j]).sum())})
  for h in range(1,13):
   target=truth[h:];b=base[:-h];pairs=np.isfinite(b)&np.isfinite(target);exp={'scheduled_rows':168-h,'boundary_exclusions':h,'observed_targets':int(np.isfinite(target).sum()),'pairs':int(pairs.sum()),'missing_truth':int(np.isnan(target).sum()),'observed_without_base':int((np.isfinite(target)&~np.isfinite(b)).sum()),'high_targets':int((target>=7).sum()),'high_pairs':int((pairs&(target>=7)).sum())};r=next(r for r in storedtargets if r['window']==label and int(r['horizon_h'])==h);ck(label+'targets'+str(h),all(int(r[k])==v for k,v in exp.items()));targetaudit.append({'window':label,'horizon_h':h,**exp});ck(label+'no bridge'+str(h),np.all(times[:-h]+h*3600==times[h:]) and times[-h]+h*3600>=ep(win['stop_exclusive']))
  np.savez_compressed(R/f'reconstructed-{label}.npz',times=times,features=F,base=base,truth=truth)
  results.append({'window':label,'origins':len(times),'cells':F.size,'missing_cells':int(np.isnan(F).sum()),'finite_base':int(np.isfinite(base).sum()),'finite_truth':int(np.isfinite(truth).sum())})
 ck('all coverage sizes',len(storedtargets)==12 and len(storedrain)==30 and len(storedfeatures)==120 and len(storedlevels)==672 and len(storedqi)==3024)
 for p,h in read(M/'preparation.json')['input_sha256'].items():ck('prepared input hash '+p,sha(W/p)==h)
 for p,h in sources.items():ck('final source hash '+p,sha(W/p)==h)
 save('independent-target-coverage.csv',targetaudit);save('independent-base-traces.csv',levelaudit);save('independent-feature-catalog.csv',featureaudit)
 result={'passed':True,'check_count':len(checks),'checks':checks,'windows':results,'total_cells':sum(r['cells'] for r in results),'maximum_absolute_difference':max(c.get('maximum_difference',0) for c in checks),'source_sha256':sources,'limits':['No fitting or model inference','Clock conversion UTC-3 is a declared computational assumption, not a source timezone contract','Source JSONL previously checked against every XML field; hashes reverified, no new parse of original XML in this matrix audit','ONS literal values and raw hashes audited; no new parse of monthly original CSV','Rain geometric integration checked independently, preserving literal timestamps, long-interval exclusions and missingness','Equivalent future training requires same declared anchor/QC contract for comparator; matrix identity does not certify generalization']}
 (R/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','source_sha256']},indent=2))
if __name__=='__main__':main()
