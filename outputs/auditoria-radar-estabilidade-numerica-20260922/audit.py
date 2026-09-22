"""Independent numeric stability experiment audit. No training or model selection."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import defaultdict
import csv,json,hashlib,math,importlib.metadata
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
E=ROOT/'outputs/experimento-radar-estabilidade-numerica-20260922';B=ROOT/'outputs/experimento-radar-observado-120-20260921';C=ROOT/'outputs/experimento-radar-historico-2020-20260921';N=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921';A=ROOT/'outputs/radar-matriz-observada-2020-20260921';M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922';V=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922';G=ROOT/'outputs/auditoria-normalizacao-radar-20260922';R=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922'
TZ=timezone(timedelta(hours=-3));families=('raw_original','raw_plus2020','normalized_original','normalized_plus2020');checks=[];sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def read(p):return json.loads(use(p).read_text())
def rows(p):return list(csv.DictReader(use(p).open()))
def dump(name,v):(P/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(name,rr):
 if rr:
  with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def ok(name,x):assert x,name;checks.append(dict(name=name,passed=True))
def eq(x,y):return np.array_equal(np.asarray(x),np.asarray(y),equal_nan=True)
def number(v):return float(v) if v not in ('',None) else np.nan
def epoch(s):return datetime.fromisoformat(s).timestamp()
def iso(t):return datetime.fromtimestamp(t,TZ).isoformat()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a).view(np.uint8)).hexdigest()
def norm(a):
 out=a[:,:120].copy();out[:,45:]=np.round(out[:,45:],8);view=out[:,45:];view[view==0]=0.;return out

def manifest(folder):
 m=read(folder/'artifact-hashes.json');it=m['files'].items() if isinstance(m,dict) else [(r['file'],r['sha256']) for r in m]
 count=0
 for f,h in it:assert sha(folder/f)==h,(folder,f);count+=1
 ok('manifest:'+str(folder.relative_to(ROOT)),True);return count

def auditmetrics(pred,saved,periods,field,dataset):
 lookup={(r['period'],int(r['horizon_h']),r['population'],r['subset'],r['family']):r for r in saved};groups=defaultdict(list)
 for r in pred:groups[str(r[field]),int(r['nominal_lead_h'])].append(r)
 result=[]
 for period in periods:
  for h in range(1,13):
   group=[r for (p,lead),rr in groups.items() if lead==h and (p==period or period=='pooled') for r in rr]
   for population in ('full_schedule','complete24','missing24'):
    pop=[r for r in group if population=='full_schedule' or (r['complete24']=='True')==(population=='complete24')];actual=np.array([number(r['actual_m']) for r in pop]);finite=np.isfinite(actual)
    for subset in ('all','level_ge_7m'):
     obs=finite&((actual>=7) if subset=='level_ge_7m' else True);nobs=int(obs.sum())
     for family in families:
      y=np.array([number(r[family+'_m']) for r in pop]);paired=obs&np.isfinite(y);err=y[paired]-actual[paired];ab=np.abs(err);npair=int(paired.sum());hits=int((ab<=.5).sum())
      x=dict(dataset=dataset,period=period,horizon_h=h,population=population,subset=subset,family=family,scheduled_rows=len(pop),missing_truth=int((~finite).sum()),observed_targets=nobs,pairs=npair,failures=nobs-npair,hits=hits,paired_hit_fraction=hits/npair if npair else None,observed_target_hit_fraction=hits/nobs if nobs else None,mae_m=float(np.mean(ab)) if npair else None,bias_m=float(np.mean(err)) if npair else None,p98_abs_m=float(np.quantile(ab,.98)) if npair else None,max_abs_m=float(np.max(ab)) if npair else None)
      r=lookup[period,h,population,subset,family]
      for k,v in x.items():
       if k in ('dataset','period','horizon_h','population','subset','family'):continue
       if v is None:assert r[k]=='',(dataset,period,h,k)
       else:assert math.isclose(v,float(r[k]),rel_tol=0,abs_tol=1e-12),(dataset,period,h,population,subset,family,k,v,r[k])
      result.append(x);ok(f'metrics:{dataset}:{period}:{h}:{population}:{subset}:{family}',True)
 ok(dataset+':metric_count',len(result)==len(saved));return result

def main():
 assert (E/'experiment.json').exists(),'Await final experiment completion; no polling/restart.'
 manifest_counts={str(f.relative_to(ROOT)):manifest(f) for f in (E,B,C,A,M,V,G,R)}
 protocol=read(E/'protocol.json');registration=read(ROOT/'docs/radar-numeric-stability-registration.json');pre=read(E/'pre-fit-manifest.json');exp=read(E/'experiment.json')
 ok('preregistered_rule_hash',sha(E/'protocol.json')==sha(ROOT/'docs/radar-numeric-stability-protocol.json')==registration['protocol_sha256'])
 ok('preregistered_helper_hash',sha(ROOT/'scripts/hydro_radar_numeric.py')==sha(E/'code/hydro_radar_numeric.py')==registration['helper_sha256']);ok('executed_runner_hash',sha(ROOT/'scripts/hydro_radar_numeric_experiment.py')==sha(E/'code/hydro_radar_numeric_experiment.py'))
 ok('registration_before_prefit_before_finish',registration['registered_at_utc']<pre['registered_at_utc']<exp['finished_at_utc'] and registration['fit_started'] is False and pre['training_started'] is False)
 ok('prefit_gate_passed',read(G/'verification.json')['pre_fit_gate_passed'] is True and pre['normalization_gate_passed'] is True)
 ok('prefit_final_inputlists_exact',pre['input_sha256']==exp['input_sha256'])
 for path,h in pre['input_sha256'].items():ok('prefit_input:'+path,sha(ROOT/path)==h)
 ok('normalized_input_hash',sha(E/'normalized-inputs.npz')==pre['normalized_inputs_sha256']);ok('runtime_match',pre['runtime']==exp['runtime']=={k:importlib.metadata.version(k) for k in pre['runtime']})
 old=dict(np.load(use(N/'features.npz')));added=dict(np.load(use(A/'features.npz')));normalized=dict(np.load(use(E/'normalized-inputs.npz')));F=old['features'][:,:120];X=norm(F);NF=added['features'];NX=norm(NF);ok('original_normalized_exact',eq(X,normalized['original']));ok('2020_normalized_exact',eq(NX,normalized['added2020']))
 t,base,truth=(old[k] for k in ('times','base','truth'));nt,nb,ny=(added[k] for k in ('times','base','truth'));masks=dict(np.load(use(C/'training-masks.npz')));bmasks=dict(np.load(use(B/'training-masks.npz')));ct={(r['phase'],int(r['horizon_h'])):r for r in rows(C/'training.csv')};bt={(r['phase'],int(r['horizon_h'])):r for r in rows(B/'training.csv')};tr={(r['phase'],r['family'],int(r['horizon_h'])):r for r in rows(E/'training.csv')};ok('48trainingrecords',len(tr)==48)
 models={};rawmodels={};memberships=[];training_arrays={};start=epoch('2025-10-01T00:00:00-03:00');cut=epoch('2026-07-01T00:00:00-03:00');stop=epoch('2026-09-21T00:00:00-03:00')
 reservation=read(ROOT/'docs/radar-historical-evaluation-reservation.json')
 for w in reservation['windows']:
  lo=epoch(w['start_inclusive_local']);hi=epoch(w['stop_exclusive_local']);ok('no2021_22_training:'+w['start_inclusive_local'],not any(((tt>=lo)&(tt<hi)).any() for tt in (t,nt)))
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)];delta=target-base;newtarget=np.r_[ny[h:],np.full(h,np.nan)];newdelta=newtarget-nb;addmask=masks[f'new_h{h}'];expectedadd=np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<epoch('2020-07-21T00:00:00-03:00'));ok(f'2020membership_h{h}',np.array_equal(addmask,expectedadd));add=np.flatnonzero(addmask)
  valid=np.isfinite(base)&np.isfinite(target);first=valid&(t+h*3600<start)
  for phase in ('validation','test'):
   mask=masks[f'{phase}_original_h{h}'];expected=first if phase=='validation' else first|(valid&(t>=start)&(t+h*3600<cut));ok(f'originalmembership:{phase}:{h}',np.array_equal(mask,expected) and np.array_equal(mask,bmasks[f'{phase}_h{h}']));train=np.flatnonzero(mask);info=ct[phase,h];ok(f'trainingcutoff:{phase}:{h}',np.all(t[train]+h*3600<epoch(info['cutoff_exclusive'])))
   for family,folder in [('original',B),('plus2020',C)]:
    raw=joblib.load(use(folder/'models'/f'{phase}-{h}.joblib'));modelpath=use(E/'models'/f'{phase}-{family}-{h}.joblib');model=joblib.load(modelpath);models[phase,family,h]=model;rawmodels[phase,family,h]=raw
    ok(f'params:{phase}:{family}:{h}',model.get_params()==raw.get_params() and model.n_features_in_==raw.n_features_in_==120);ok(f'initial_prediction_same:{phase}:{family}:{h}',eq(model._baseline_prediction,raw._baseline_prediction));ok(f'niterations_same:{phase}:{family}:{h}',model.n_iter_==raw.n_iter_==180)
    if family=='original':xf=X[train];yf=delta[train];levels=target[train];order=t[train]
    else:xf=np.vstack([NX[add],X[train]]);yf=np.r_[newdelta[add],delta[train]];levels=np.r_[newtarget[add],target[train]];order=np.r_[nt[add],t[train]]
    ww=1+2*(abs(yf)>=1)+2*(levels>=9);ok(f'chronology_finite_labels_weights:{phase}:{family}:{h}',np.all(np.diff(order)>0) and np.isfinite(yf).all() and set(np.unique(ww))<=set((1,3,5)))
    saved=tr[phase,family,h];control=bt[phase,h] if family=='original' else info;expectedcounts=dict(original_n=len(train),added_n=len(add) if family=='plus2020' else 0,n=len(yf));ok(f'training_counts:{phase}:{family}:{h}',all(int(saved[k])==v for k,v in expectedcounts.items()) and int(control['n'])==len(yf))
    ok(f'leaf_loss_cutoff:{phase}:{family}:{h}',saved['loss']==model.loss==control['loss'] and int(saved['leaf_nodes'])==model.max_leaf_nodes==int(control['leaf_nodes']) and saved['cutoff_exclusive']==control['cutoff_exclusive'] and saved['latest_training_target']==control['latest_training_target'])
    # Record independently reconstructed arrays; neither model stores full sample rows/weights.
    tag=f'{phase}-{family}-{h}';training_arrays[tag+':origin']=order;training_arrays[tag+':delta']=yf;training_arrays[tag+':weight']=ww
    memberships.append(dict(phase=phase,family=family,horizon_h=h,**expectedcounts,weight_sum=int(ww.sum()),weight1=int((ww==1).sum()),weight3=int((ww==3).sum()),weight5=int((ww==5).sum()),features_sha256=ah(xf),deltas_sha256=ah(yf),weights_sha256=ah(ww),ordered_origins_sha256=ah(order),initial_prediction=float(model._baseline_prediction.ravel()[0]),latest_training_target=saved['latest_training_target'],cutoff_exclusive=saved['cutoff_exclusive']))
 np.savez_compressed(P/'reconstructed-training-order-targets-weights.npz',**training_arrays)
 oldpred=rows(C/'predictions.csv');pred=rows(E/'predictions.csv');key=lambda r:(r['phase'],r['origin'],int(r['nominal_lead_h']));lookup={key(r):r for r in oldpred};current={key(r):r for r in pred};ok('102084original_keys',len(pred)==len(current)==len(lookup)==102084 and set(current)==set(lookup))
 for k,r in current.items():
  oldr=lookup[k];assert all(r[f]==oldr[f] for f in ('origin','target_time','base_m','actual_m'));assert r['raw_original_m']==oldr['observed_control_m'] and r['raw_plus2020_m']==oldr['augmented_m']
 ok('original_labels_rawcontrols_exact',True);replay=[]
 for phase,left,right in [('validation',start,cut),('test',cut,stop)]:
  for h in range(1,13):
   scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));ss=[current[phase,iso(t[i]),h] for i in scheduled];base0=base[scheduled];target=np.r_[truth[h:],np.full(h,np.nan)][scheduled];finite=np.isfinite(base0);ok(f'original_source_labels:{phase}:{h}',eq([number(r['base_m']) for r in ss],base0) and eq([number(r['actual_m']) for r in ss],target));ok(f'original_complete24:{phase}:{h}',all((r['complete24']=='True')==bool(old['complete24'][i]) for i,r in zip(scheduled,ss)))
   for family in ('original','plus2020'):
    for kind,model,features in [('raw',rawmodels[phase,family,h],F),('normalized',models[phase,family,h],X)]:
     yy=np.full(len(ss),np.nan);yy[finite]=model.predict(features[scheduled[finite]])+base0[finite];saved=np.array([number(r[kind+'_'+family+'_m']) for r in ss]);ok(f'inference:{phase}:{kind}:{family}:{h}',eq(yy,saved));ok(f'base_only_gate:{phase}:{kind}:{family}:{h}',np.array_equal(np.isfinite(saved),finite));replay.append(dict(dataset='original',period=phase,kind=kind,family=family,horizon_h=h,rows=len(ss),applied=int(finite.sum()),max_difference_m=0.))
 previous=rows(R/'predictions.csv');reused=rows(E/'reused-2021-2022-predictions.csv');key=lambda r:(int(r['year']),r['origin'],int(r['nominal_lead_h']));rrlookup={key(r):r for r in previous};rrcurrent={key(r):r for r in reused};ok('26340reused_keys',len(reused)==len(rrcurrent)==len(rrlookup)==26340 and set(rrlookup)==set(rrcurrent))
 for k,r in rrcurrent.items():
  oldr=rrlookup[k];assert all(r[f]==oldr[f] for f in ('origin','target_time','base_m','actual_m','complete24'));assert r['raw_original_m']==oldr['control120_m'] and r['raw_plus2020_m']==oldr['candidate120_plus2020_m']
 ok('reused_labels_rawcontrols_exact',True);stability=[]
 for year in (2021,2022):
  d=dict(np.load(use(M/str(year)/'features.npz')));v=dict(np.load(use(V/f'reconstructed-{year}.npz')));xx=norm(d['features']);vv=norm(v['features']);ok(f'normalized_orig_reconstruction:{year}',eq(xx,vv) and eq(xx,normalized[f'year{year}']));n=len(d['times'])
  for h in range(1,13):
   ss=[rrcurrent[year,iso(t0),h] for t0 in d['times'][:n-h]];base0=d['base'][:n-h];target=d['truth'][h:];finite=np.isfinite(base0);ok(f'reused_source_labels:{year}:{h}',eq([number(r['base_m']) for r in ss],base0) and eq([number(r['actual_m']) for r in ss],target))
   for family in ('original','plus2020'):
    m=models['test',family,h];one=np.full(len(ss),np.nan);two=one.copy();one[finite]=m.predict(xx[:n-h][finite])+base0[finite];two[finite]=m.predict(vv[:n-h][finite])+base0[finite];saved=np.array([number(r['normalized_'+family+'_m']) for r in ss]);ok(f'reused_inference:{year}:{family}:{h}',eq(one,saved));ok(f'reconstructed_inference:{year}:{family}:{h}',eq(one,two));ok(f'reused_missingness:{year}:{family}:{h}',np.array_equal(np.isfinite(saved),finite));stability.append(dict(year=year,family=family,horizon_h=h,predictions=int(finite.sum()),maximum_difference_m=0.))
 ok('48_stability_applications',len(stability)==48);savedstab=rows(E/'reconstruction-stability.csv');ok('stability_report_exact',all(all(str(s[k])==str(r[k]) for k in s) for s,r in zip(stability,savedstab)))
 metrics=auditmetrics(pred,rows(E/'evaluation.csv'),('validation','test'),'phase','original')+auditmetrics(reused,rows(E/'reused-2021-2022-evaluation.csv'),('2021','2022','pooled'),'year','reused_development');ok('1440_metrics',len(metrics)==1440)
 index={(r['dataset'],r['period'],r['horizon_h'],r['population'],r['subset'],r['family']):r for r in metrics};changes=[];tallies=[]
 for dataset,periods in [('original',('validation','test')),('reused_development',('2021','2022','pooled'))]:
  for period in periods:
   for subgroup in ('all','level_ge_7m'):
    for membership in ('original','plus2020'):
     group=[]
     for h in range(1,13):
      a=index[dataset,period,h,'full_schedule',subgroup,'raw_'+membership];b=index[dataset,period,h,'full_schedule',subgroup,'normalized_'+membership]
      d=dict(dataset=dataset,period=period,subset=subgroup,membership=membership,horizon_h=h,observed_targets=a['observed_targets'],pairs=a['pairs'],failures=a['failures'],raw_hits=a['hits'],normalized_hits=b['hits'],hit_change=b['hits']-a['hits'],raw_mae=a['mae_m'],normalized_mae=b['mae_m'],mae_change=b['mae_m']-a['mae_m'],raw_max=a['max_abs_m'],normalized_max=b['max_abs_m'],max_change=b['max_abs_m']-a['max_abs_m']);changes.append(d);group.append(d)
     tallies.append(dict(dataset=dataset,period=period,subset=subgroup,membership=membership,hits_gain_h=[r['horizon_h'] for r in group if r['hit_change']>0],hits_loss_h=[r['horizon_h'] for r in group if r['hit_change']<0],mae_worse_h=[r['horizon_h'] for r in group if r['mae_change']>0],max_worse_h=[r['horizon_h'] for r in group if r['max_change']>0]))
 for path,h in pre['input_sha256'].items():assert sha(ROOT/path)==h,path
 ok('normalized_input_hash_unchanged_after_audit',sha(E/'normalized-inputs.npz')==pre['normalized_inputs_sha256']);ok('48models_no_promotion',exp['models_fitted']==48 and exp['promoted'] is False and exp['training_membership_changed'] is False)
 report=dict(passed=True,checks=checks,source_sha256=sources,manifest_counts=manifest_counts,prefit_inputs_verified=len(pre['input_sha256']),normalized_input_sha256=pre['normalized_inputs_sha256'],models_audited=48,original_control_applications_exact=48,original_normalized_applications_exact=48,reused_normalized_applications_exact=48,reconstructed_applications_identical=48,original_schedule_rows=102084,reused_development_rows=26340,metrics_verified=1440,training=memberships,tallies=tallies,time_order=dict(registered=registration['registered_at_utc'],prefit_manifest=pre['registered_at_utc'],finished=exp['finished_at_utc']),limitations=['No fit/tuning, external lookup or operational action in this audit.','Membership/order/targets/weights reconstructed from frozen masks/formula and executed source; fittedmodels do not retain full sample weights. Initial predictions and parameters are identical to paired raw controls.','No separate fit-start event exists: preregistration/prefit record and code order verified, not a global execution-history certificate.','2021/2022 are explicitly reused development after first challenge, never a new independent test.','Numerical reproducibility is not hydrological accuracy; source timestamp/datum/availability limits remain.','No horizon-specific model mixing or promotion.'])
 dump('verification.json',report);save('training-reconstruction.csv',memberships);save('inference-replay.csv',replay);save('reconstruction-stability.csv',stability);save('independent-metrics.csv',metrics);save('normalization-effects.csv',changes);dump('source-manifest.json',sources)
 lines=['# Auditoria independente — estabilidade numérica RADAR','',f'{len(checks)} verificações passaram. Foram auditados 48 modelos novos, preservando máscaras, ordem, pesos reconstruídos e parâmetros dos controles correspondentes. Reprodução exata de 48 controles, 48 aplicações novas no acervo original e 48 no acervo reutilizado; as 48 reaplicações sobre reconstruções normalizadas são idênticas.','', 'Conferidas 102.084 linhas originais, 26.340 linhas de desenvolvimento reutilizado e 1.440 métricas. Ausências de previsão contam contra alvos observados; truth ausente permanece desconhecido.','', 'normalization-effects.csv compara apenas mesma membership antes/depois da normalização. training-reconstruction.csv e NPZ registram os alvos, ordem e pesos reconstruídos; sem novo ajuste.','',*report['limitations']]
 (P/'README.md').write_text('\n'.join(lines)+'\n');dump('artifact-hashes.json',[dict(file=str(p.relative_to(P)),sha256=sha(p)) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']);print(json.dumps(dict(passed=True,checks=len(checks),inputs=len(pre['input_sha256']),tallies=tallies),indent=2),flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=2):main()
