"""Independent artifact/causal-boundary audit; does not fit models or score errors."""
from pathlib import Path
from datetime import datetime,timezone
import ast,csv,hashlib,json,math
import numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=ROOT/'outputs/verificacao-sem-monte-20260921'
RUN=ROOT/'outputs/experimento-sem-monte-20260921';FLOW=ROOT/'outputs/experimento-niveis-reservatorios-20260921';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
REMOVED=list(range(8,16))+list(range(61,69));CHECKS=[];HASHES={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):HASHES[str(p)]=sha(p);return p
def js(p):return json.loads(read(p).read_text())
def rows(p):return list(csv.DictReader(read(p).open()))
def check(k,v,detail=None):CHECKS.append(dict(check=k,passed=bool(v),detail=detail))
def epoch(s):return datetime.fromisoformat(s).timestamp()
def iso(x):return datetime.fromtimestamp(float(x),timezone.utc).isoformat()
def shift(a,k):
 v=np.full(a.shape,np.nan)
 if k>0:v[k:]=a[:-k]
 elif k<0:v[:k]=a[-k:]
 else:v[:]=a
 return v
def infer(m,x):
 z=np.column_stack([np.where(np.isfinite(x),x,m['median']),~np.isfinite(x)])
 return (z-m['mean'])/m['scale']@m['beta']+m['intercept']
def key(r):return int(r['lead_h']),r['phase'],r['origin'],r['target_time']
def run():
 if not (RUN/'experiment.json').exists():print('WAITING_EXPERIMENT');return
 OUT.mkdir(exist_ok=True,parents=True)
 meta=js(RUN/'experiment.json');policy=js(RUN/'protocol.json');original=js(FLOW/'experiment.json')
 for name,digest in meta['input_sha256'].items():
  p=Path(name);check('input hash '+name,sha(read(p))==digest)
  if p.suffix=='.py':check('executed code snapshot '+p.name,sha(read(RUN/'code'/p.name))==digest)
 check('protocol matches source',sha(RUN/'protocol.json')==sha(read(ROOT/'docs/monte-ablation-protocol.json')))
 expectedpaths={str(ROOT/'docs/monte-ablation-protocol.json'),str(BASE/'dados-roteamento.npz'),str(BASE/'telemetria-latencia.npz'),str(FLOW/'additional-features.npz'),str(FLOW/'frozen-models.json'),str(FLOW/'predictions.csv'),str(FLOW/'artifact-hashes.json'),str(FLOW/'experiment.json'),*[str(ROOT/'scripts'/n) for n in ['hydro_monte_ablation.py','hydro_hourly_forecast.py','hydro_hourly_models.py','hydro_upstream_audit.py','hydro_upstream_tree_experiment.py','hydro_routing_fit.py']]}
 check('all expected input paths',set(meta['input_sha256'])==expectedpaths)
 for item in js(FLOW/'artifact-hashes.json'):
  p=FLOW/item['file']
  if p.name in ['additional-features.npz','frozen-models.json','predictions.csv','experiment.json','input-trace.csv']:check('original manifest '+p.name,sha(read(p))==item['sha256'])
 d=dict(np.load(read(BASE/'dados-roteamento.npz')));z=dict(np.load(read(BASE/'telemetria-latencia.npz')));extra=dict(np.load(read(FLOW/'additional-features.npz')))
 t=d['times'];ix=np.searchsorted(z['times'],t)
 check('hourly grid match',np.array_equal(t,z['times'][ix]) and np.array_equal(t,extra['times']) and np.all(np.diff(t)==3600))
 cols=[];names=[]
 for source in ['julho:Q','julho:I','monte:Q','monte:I','castro:Q','castro:I','86500000:Q']:
  a=z[source][ix]/1000;cols.extend([a,a-shift(a,1),(a-shift(a,3))/3,(a-shift(a,6))/6]);names.extend([source+':'+k for k in ['current','change1','slope3','slope6']])
 groups=['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']
 for group in groups:
  for w in [3,6,12,24,48]:cols.append(z[group+f':P{w}'][ix]/100);names.append(group+f':P{w}')
 F53=np.column_stack(cols)
 # Compare independent construction with the exact preserved upstream_features function.
 tree=ast.parse((RUN/'code/hydro_hourly_models.py').read_text());fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='upstream_features')
 env={'np':np,'shift':shift,'GROUPS':groups};exec(compile(ast.Module(body=[fun],type_ignores=[]),'snapshot-upstream-features','exec'),env)
 check('53 columns independently reproduced',np.array_equal(F53,env['upstream_features'](z,t),equal_nan=True))
 expectednames=[f'{plant}:{field}:{kind}' for plant in ['julho','monte','castro'] for field in ['val_nivelmontante','val_niveljusante'] for kind in ['level','change1','slope3','slope6']]
 check('additional_feature_names physical order',original['additional_feature_names']==expectednames)
 names+=expectednames;F=np.column_stack([F53,extra['levels_and_slopes']]);X=np.delete(F,REMOVED,axis=1)
 check('removed columns exclusively Monte',REMOVED==[i for i,n in enumerate(names) if n.startswith('monte:')])
 check('dimensions77to61',F.shape[1]==77 and X.shape[1]==61)
 check('protocol removes expected16',policy['removed_columns']==REMOVED and meta['removed_columns']==REMOVED)
 (OUT/'removed-columns.json').write_text(json.dumps([{'index':i,'name':names[i]} for i in REMOVED],indent=2)+'\n')
 trace=rows(FLOW/'input-trace.csv')
 # Trace-to-array equality and lag definition check for all 24 additional columns.
 for plant in ['julho','monte','castro']:
  for field in ['val_nivelmontante','val_niveljusante']:
   tr=[r for r in trace if r['plant']==plant and r['field']==field]
   mapping={epoch(r['origin']):float(r['value_m']) if r['value_m'] else np.nan for r in tr}
   v=np.array([mapping.get(x,np.nan) for x in t])
   for j,a in enumerate([v,v-shift(v,1),(v-shift(v,3))/3,(v-shift(v,6))/6]):
    name=f'{plant}:{field}:'+['level','change1','slope3','slope6'][j];idx=expectednames.index(name)
    check('source trace and lag '+name,np.array_equal(a,extra['levels_and_slopes'][:,idx],equal_nan=True))
 source=(RUN/'code/hydro_monte_ablation.py').read_text();tree=ast.parse(source);fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='without_monte')
 env={'np':np,'REMOVED':REMOVED};exec(compile(ast.Module(body=[fun],type_ignores=[]),'snapshot-ablation','exec'),env)
 check('ablation retains exactly other61 columns',np.array_equal(env['without_monte'](F),X,equal_nan=True))
 models=js(RUN/'frozen-models.json');oldmodels=js(FLOW/'frozen-models.json')
 check('48 models, only Julho',len(models)==48 and all(k.startswith('julho:') for k in models))
 pred=rows(RUN/'predictions.csv');oldrows=[r for r in rows(FLOW/'predictions.csv') if r['source']=='julho' and r['family']=='level_and_slopes']
 oldmap={key(r):r for r in oldrows};families={fam:{key(r):r for r in pred if r['family']==fam} for fam in ['level_and_slopes','without_monte']}
 check('no duplicate prediction keys',sum(len(v) for v in families.values())==len(pred))
 check('same family pairs and preserved original coverage',set(families['level_and_slopes'])==set(families['without_monte'])==set(oldmap))
 check('both families same targets/high labels',all(all(families[fam][k]['actual_m3_s']==oldmap[k]['actual_m3_s'] and families[fam][k]['high_flow']==oldmap[k]['high_flow'] for k in oldmap) for fam in families))
 check('all predictions finite no lost coverage',all(math.isfinite(float(r['forecast_m3_s'])) for r in pred))
 maxold=max(abs(float(r['forecast_m3_s'])-float(oldmap[k]['forecast_m3_s'])) for k,r in families['level_and_slopes'].items())
 check('original77 predictions reproduced',maxold<=1e-7,{'max_absolute_difference_m3_s':maxold,'rows':len(oldmap)})
 known=z['julho:Q'][ix]/1000
 boundaries=[epoch('2025-10-01T00:00:00-03:00'),epoch('2026-07-01T00:00:00-03:00'),epoch('2026-09-21T00:00:00-03:00')]
 training={(int(r['lead_h']),r['phase']):r for r in rows(RUN/'training.csv')}
 replaymax=0.;equationmax=0.
 for lead in range(12):
  target=shift(d['julho'],-lead);good=np.isfinite(target)&np.isfinite(known);delta=target-known
  for phase,cutoff,end in [('validation',boundaries[0],boundaries[1]),('test',boundaries[1],boundaries[2])]:
   train=np.where(good&(t+lead*3600<cutoff))[0];apply=np.where(good&(t>=cutoff)&(t+lead*3600<end))[0];r=training[lead,phase]
   check(f'{lead}/{phase}: strict train cutoff and counts',int(r['training_n'])==len(train) and int(r['evaluation_n'])==len(apply) and epoch(r['latest_training_target'])==float(max(t[train]+lead*3600)) and epoch(r['cutoff_exclusive'])==cutoff and np.all(t[train]+lead*3600<cutoff))
   expectedkeys={(lead,phase,float(t[i]),float(t[i]+lead*3600)) for i in apply}
   for fam in families:
    actualkeys={(k[0],k[1],epoch(k[2]),epoch(k[3])) for k in families[fam] if k[0]==lead and k[1]==phase}
    check(f'{lead}/{phase}/{fam}: independent partition exact',actualkeys==expectedkeys)
    mk=f'julho:{lead}:{phase}:{fam}';m={k:np.asarray(v) if isinstance(v,list) else v for k,v in models[mk].items()};A=F if fam=='level_and_slopes' else X;nf=A.shape[1]
    check(mk+': model dimensions',m['median'].shape==(nf,) and all(m[k].shape==(2*nf,) for k in ['mean','scale','beta']))
    if fam=='level_and_slopes':check(mk+': original frozen model content',models[mk]==oldmodels[mk])
    else:
     med=np.array([np.nanmedian(A[train,j]) if np.isfinite(A[train,j]).any() else 0 for j in range(nf)])
     matrix=np.column_stack([np.where(np.isfinite(A[train]),A[train],med),~np.isfinite(A[train])]);mean=matrix.mean(0);scale=matrix.std(0);scale[scale<1e-8]=1
     weights=1+2*(target[train]>2);weights=weights/weights.mean();ym=np.average(delta[train],weights=weights)
     check(mk+': training-only preprocessing',np.array_equal(med,m['median']) and np.array_equal(mean,m['mean']) and np.array_equal(scale,m['scale']) and abs(ym-m['intercept'])<1e-12)
     B=(matrix-mean)/scale;lhs=(np.einsum('ni,n,nj->ij',B,weights,B)+1000*np.eye(2*nf))@m['beta'];rhs=np.einsum('ni,n,n->i',B,weights,delta[train]-ym);rel=float(np.max(abs(lhs-rhs))/(1+np.max(abs(rhs))));equationmax=max(equationmax,rel)
     check(mk+': frozen solution matches alpha1000 weighted normal equation',rel<=1e-9,{'relative_residual':rel})
    actual=np.maximum(known[apply]+infer(m,A[apply]),0)*1000
    saved={epoch(k[2]):float(r['forecast_m3_s']) for k,r in families[fam].items() if k[0]==lead and k[1]==phase}
    err=float(max(abs(actual-np.array([saved[float(t[i])] for i in apply]))));replaymax=max(replaymax,err)
    check(mk+': independent inference',err<=1e-7,{'max_difference_m3_s':err})
 # Ensure this audit did not race modifications.
 check('all audited inputs remain unchanged',all(sha(Path(k))==v for k,v in HASHES.items()))
 failures=[r['check'] for r in CHECKS if not r['passed']]
 result={'passed':not failures,'checks':CHECKS,'failure_count':len(failures),'failures':failures,'input_sha256':HASHES,'prediction_rows':len(pred),'rows_per_family':len(oldmap),'models77':24,'models61':24,'original_reproduction_max_m3_s':maxold,'independent_inference_max_m3_s':replaymax,'normal_equation_max_relative_residual':equationmax,'fitted_here':False,'metrics_calculated':False,'causality_certified':False,'limitations':['Original historical publication and source latency are assumed.','Monte columns removed are direct predictors; other sources can retain physically correlated information.','Original evaluation.csv helper emits n/MAE/bias/P90; the main agent has supplied evaluation-extended.csv with RMSE/P98/maximum. This audit does not recalculate performance metrics.','Previously inspected development periods are not an independent holdout.'],'created_at_utc':datetime.now(timezone.utc).isoformat()}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['passed','failure_count','failures','prediction_rows','rows_per_family','original_reproduction_max_m3_s','independent_inference_max_m3_s','normal_equation_max_relative_residual']},indent=2))
 if failures:raise SystemExit(1)
if __name__=='__main__':
 with threadpool_limits(limits=2):run()

