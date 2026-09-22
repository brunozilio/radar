"""Independent recent hourly-anchor matrix audit; no training or production imports."""
from pathlib import Path
import json,csv,hashlib,datetime as dt,ast
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];M=W/'outputs/radar-matriz-recente-ancora-horaria-20260922';S=W/'outputs/auditoria-contrato-qc-recente-2018-20260922';E=W/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921';B=W/'outputs/mucum-atualizacao-15h-2026-09-21';OLD=W/'outputs/radar-matrizes-observadas-2018-20260922';TZ=dt.timezone(dt.timedelta(hours=-3));checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):inputs[str(p.relative_to(W))]=sha(p);return p
def read(p):return json.loads(use(p).read_text())
def ck(name,b):assert b,name;checks.append({'check':name,'passed':True})
def compare(name,a,b):
 a=np.asarray(a);b=np.asarray(b);ck(name+'shape',a.shape==b.shape);ck(name+'NaNmask',np.array_equal(np.isnan(a),np.isnan(b)));equal=np.array_equal(a,b,equal_nan=True);finite=np.isfinite(a)&np.isfinite(b);diff=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0
 checks.append({'check':name,'passed':equal,'cells':int(a.size),'maximum_absolute_difference':diff});assert equal,name
def ep(s):return dt.datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp()
def iso(t):return dt.datetime.fromtimestamp(float(t),TZ).isoformat()
def back(a,n):return np.r_[np.full(n,np.nan),a[:-n]]
def asof(t,v,q,age):
 ix=np.searchsorted(t,q,side='right')-1;out=np.full(len(q),np.nan)
 if len(t):good=(ix>=0)&(q-t[np.maximum(ix,0)]<=age);out[good]=v[ix[good]]
 return out,ix
def save(name,rows):
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def manifest(folder,name):
 m=read(folder/name);items=m['files'] if isinstance(m,dict) else m
 for r in items:ck('hash '+str(folder.relative_to(W))+'/'+r['file'],sha(folder/r['file'])==r['sha256'])
def main():
 for d,f in [(M,'artifact-hashes.json'),(S,'manifest.json'),(OLD,'artifact-hashes.json')]:manifest(d,f)
 protocol=read(W/'docs/radar-recent-hourly-anchor-features-protocol.json');aug=read(W/'docs/radar-2018-hourly-augmentation-protocol.json');use(W/'scripts/hydro_radar_recent_hourly_anchor.py');use(W/'scripts/hydro_radar_2018_augmentation.py')
 D=dict(np.load(use(M/'features.npz')));Q=dict(np.load(use(M/'quarter-hour.npz')));prev=dict(np.load(use(E/'features.npz')));z=dict(np.load(use(B/'telemetria-latencia.npz')));keep=prev['times']<ep('2026-09-21');t=prev['times'][keep];grid=z['times'];ix=np.searchsorted(grid,t)
 compare('timegrid',t,D['times']);compare('quartergrid',grid,Q['times']);ck('shape12912x120',D['features'].shape==(12912,120));ck('hourly_contiguous',np.all(np.diff(t)==3600));compare('columns6to119_frozen',D['features'][:,6:120],prev['features'][keep,6:120])
 cols=[];names=[];traces=[]
 for code,lag,maxage in [('86510000',3600,0),('86472000',1800,900),('86472600',900,900),('86500000',1800,900)]:
  d=dict(np.load(use(S/'strict-latest'/f'ana-{code}.npz')));ts=d['times'];v=d['level'];ck(code+'validmask',np.array_equal(np.isfinite(v),d['level_finite']));ck(code+'explicitQCfinite',np.all(d['level_qc_approved'][np.isfinite(v)]))
  raw,_=asof(ts,v,grid,0);compare(code+' rawquarter',raw,Q['raw:'+code+':H'])
  if code=='86510000':
   whole=np.array([dt.datetime.fromtimestamp(float(s),TZ).minute==0 and dt.datetime.fromtimestamp(float(s),TZ).second==0 for s in ts]);ts=ts[whole];v=v[whole]
  h,selected=asof(ts,v,grid-lag,maxage);compare(code+' delayedquarter',h,Q[code+':H']);cols.append(h[ix]);names.append(code+':H')
  for dh in [.5,1,2,4,8]:cols.append(((h-back(h,int(dh*4)))/dh)[ix]);names.append(code+f':dH{dh}')
  if code=='86510000':
   base=h[ix];truth=raw[ix];compare('base_exact60',base,D['base']);compare('truth_exact_strict',truth,D['truth']);compare('truth_matches_original',truth,prev['truth'][keep]);ck('whole_hour_nohalf',np.isnan(cols[1]).all())
   for k,o in enumerate(t):
    j=selected[ix[k]];q=o-3600;source=ts[j] if j>=0 else None;usable=j>=0 and source==q and np.isfinite(v[j]);ck('Mu_exact_preorigin_'+str(k),source is None or source<o)
    traces.append({'origin_assumed_brt':iso(o),'query_assumed_brt':iso(q),'source_assumed_brt':iso(source) if source is not None else '', 'usable':bool(usable),'base_m':float(base[k]) if np.isfinite(base[k]) else None,'truth_m':float(truth[k]) if np.isfinite(truth[k]) else None})
 compare('first24_independent',np.column_stack(cols),D['features'][:,:24]);compare('complete24',np.isfinite(D['features'][:,:24]).all(1).astype(float),D['complete24'].astype(float));ck('complete24none',not D['complete24'].any())
 # All non-Mu quarter-hour fields equal the original snapshot; rain is not rounded.
 for key in Q:
  if key not in ('times','86510000:H'):compare('quarter_frozen_'+key,z[key],Q[key])
 catalog=read(OLD/'feature-catalog.json');counts=list(csv.DictReader(use(M/'feature-coverage.csv').open()));catrows=[]
 for j,name in enumerate(catalog):
  r=next(r for r in counts if int(r['column'])==j);ck('coverage'+str(j),int(r['finite'])==np.isfinite(D['features'][:,j]).sum() and int(r['missing'])==np.isnan(D['features'][:,j]).sum());catrows.append({'column':j,'name':name,'finite':int(np.isfinite(D['features'][:,j]).sum()),'missing':int(np.isnan(D['features'][:,j]).sum())})
 old=[dict(np.load(use(OLD/f'{label}-features.npz'))) for label in ['2018-08-30','2018-09-30']];configs=list(csv.DictReader(use(B/'previsao-atualizada.csv').open()));plans=[];targets=[];start=ep('2025-10-01');end=ep('2026-07-01');stop=ep('2026-09-21');masks={}
 for horizon in range(1,13):
  target=np.r_[truth[horizon:],np.full(horizon,np.nan)];delta=target-base;finite=np.isfinite(base)&np.isfinite(target);initial=finite&(t+horizon*3600<start);later=finite&(t>=start)&(t+horizon*3600<end);extra_y=[];extra_target=[]
  ck('configuration'+str(horizon),configs[horizon-1]['model']=='arvores_previsao_chuva' and int(float(configs[horizon-1]['lead_h']))==horizon)
  leaf,loss=ast.literal_eval(configs[horizon-1]['parameters'])
  for j,d in enumerate(old):
   ny=np.r_[d['truth'][horizon:],np.full(horizon,np.nan)];nb=d['base'];mask=np.isfinite(nb)&np.isfinite(ny);ck('oldno_bridge'+str((j,horizon)),not mask[-horizon:].any());extra_y.append((ny-nb)[mask]);extra_target.append(ny[mask]);masks[f'old{j}_h{horizon}']=mask
  ey=np.concatenate(extra_y);et=np.concatenate(extra_target);ew=1+2*(abs(ey)>=1)+2*(et>=9)
  for phase,mask,left,right in [('validation',initial,start,end),('test',initial|later,end,stop)]:
   masks[f'{phase}_h{horizon}']=mask;train=np.flatnonzero(mask);schedule=(t>=left)&(t+horizon*3600<right);ck('cutoff'+str((phase,horizon)),np.all(t[mask]+horizon*3600<left));weight=1+2*(abs(delta[mask])>=1)+2*(target[mask]>=9)
   plans.append({'phase':phase,'horizon_h':horizon,'recent_rows':len(train),'2018_rows':len(ey),'control_weight_sum':int(weight.sum()),'2018_weight_sum':int(ew.sum()),'augmented_rows':len(train)+len(ey),'augmented_weight_sum':int(weight.sum()+ew.sum()),'recent_with_missing_aux18':int((~np.isfinite(D['features'][mask,6:24]).all(1)).sum()),'latest_recent_target':iso((t[mask]+horizon*3600).max()),'cutoff_exclusive':iso(left),'leaf_nodes':leaf,'loss':loss})
   observed=schedule&np.isfinite(target);pairs=observed&np.isfinite(base);high=observed&(target>=7)
   targets.append({'phase':phase,'horizon_h':horizon,'scheduled':int(schedule.sum()),'observed':int(observed.sum()),'missing_truth':int((schedule&~np.isfinite(target)).sum()),'pairs':int(pairs.sum()),'observed_missing_base':int((observed&~np.isfinite(base)).sum()),'high_observed':int(high.sum()),'high_pairs':int((high&np.isfinite(base)).sum())})
 ck('102084schedule',sum(r['scheduled'] for r in targets)==102084)
 for path,h in read(M/'preparation.json')['input_sha256'].items():ck('prepared_input '+path,sha(Path(path))==h)
 for path,h in inputs.items():ck('input_final '+path,sha(W/path)==h)
 save('mucum-source-traces.csv',traces);save('feature-catalog.csv',catrows);save('training-support.csv',plans);save('evaluation-target-support.csv',targets);np.savez_compressed(R/'expected-training-masks.npz',**masks)
 result={'passed':True,'check_count':len(checks),'checks':checks,'shape':list(D['features'].shape),'finite_base':int(np.isfinite(base).sum()),'finite_truth':int(np.isfinite(truth).sum()),'nan_cells':int(np.isnan(D['features']).sum()),'columns6to119_exact':True,'truth_original_exact':True,'non_mucum_quarter_fields_original_exact':True,'maximum_difference':max(c.get('maximum_absolute_difference',0) for c in checks),'source_sha256':inputs,'planned_fits_reviewed_not_executed':48,'evaluation_scheduled_rows':sum(r['scheduled'] for r in targets),'limits':['Only matrix/contract and planned memberships reviewed; no fitted model artifact or predictions exist in this audit','Historical publication/timezone/datum not certified','Source audit already sealed; this audit rechecks hashes and reconstructed strict NPZ values','QC/latest literal happened not to change source values; exact60min anchor and halfhour predictor removal do change training recipe','Old2018 evaluation/target shifts separate for each window; no chronological bridge']}
 (R/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_sha256')},indent=2))
if __name__=='__main__':main()
