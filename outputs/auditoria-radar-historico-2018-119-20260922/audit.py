"""Independent119-feature experiment audit: no fit/network/operational imports."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib,datetime as dt,ast,importlib.metadata
import numpy as np,joblib
from threadpoolctl import threadpool_limits
R=Path(__file__).resolve().parent;W=R.parents[1];E=W/'outputs/experimento-radar-historico-2018-119-20260922';FAILED=W/'outputs/experimento-radar-historico-2018-20260922';M=W/'outputs/radar-matriz-recente-ancora-horaria-20260922';O=W/'outputs/radar-matrizes-observadas-2018-20260922';F=('hourly_control','hourly_plus2018');checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):inputs[str(p.resolve())]=sha(p);return p
def js(p):return json.loads(use(p).read_text())
def cr(p):return list(csv.DictReader(use(p).open()))
def nz(p):return dict(np.load(use(p)))
def ck(name,b):checks.append({'check':name,'passed':bool(b)});assert b,name
def eq(a,b):return np.array_equal(a,b,equal_nan=True)
def num(x):return float(x) if x not in (None,'') else np.nan
def ep(s):return dt.datetime.fromisoformat(s).timestamp()
def iso(t):return dt.datetime.fromtimestamp(float(t),dt.timezone(dt.timedelta(hours=-3))).isoformat()
def dump(name,o):(R/name).write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def save(name,rows):
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 exp=js(E/'experiment.json');pre=js(E/'pre-fit-manifest.json');proto=W/'docs/radar-2018-hourly-augmentation-119-protocol.json';js(proto);ck('protocol bound',sha(proto)=='69fe4433ade7cea1e561b9b8558a224745f6b78c23f3b613667400b8d2dc470d');ck('recorded local ordering',dt.datetime.fromisoformat(pre['recorded_at_utc'])<dt.datetime.fromisoformat(exp['completed_at_utc']))
 ck('runtime',exp['runtime']==pre['runtime']=={k:importlib.metadata.version(k) for k in exp['runtime']})
 for meta in [pre,exp]:
  for p,h in meta['input_sha256'].items():ck('input hash '+p,sha(use(Path(p)))==h)
  for p,h in meta['prepared_sha256'].items():ck('prepared hash '+p,sha(use(E/p))==h)
 for d in [E,M,O]:
  for r in js(d/'artifact-hashes.json'):ck('artifact '+d.name+'/'+r['file'],sha(use(d/r['file']))==r['sha256'])
 masks=nz(E/'training-masks.npz');vectors=nz(E/'training-vectors.npz');prior_masks=nz(FAILED/'training-masks.npz');prior_vectors=nz(FAILED/'training-vectors.npz');ck('48masks144vectors',len(masks)==48 and len(vectors)==144 and set(masks)==set(prior_masks) and set(vectors)==set(prior_vectors))
 for k in masks:ck('failed attempt mask '+k,eq(masks[k],prior_masks[k]))
 for k in vectors:ck('failed attempt vector '+k,eq(vectors[k],prior_vectors[k]))
 plan=cr(E/'training-plan.csv');ck('48plans unchanged',len(plan)==48 and plan==cr(FAILED/'training-plan.csv'));planmap={(r['phase'],r['family'],int(r['horizon_h'])):r for r in plan}
 projection=np.load(use(E/'feature-indices.npy'));ck('fixed119projection',eq(projection,np.r_[0,np.arange(2,120)]));D=nz(M/'features.npz');old=[nz(O/f'{label}-features.npz') for label in ['2018-08-30','2018-09-30']];t=D['times'];base=D['base'];truth=D['truth'];X=D['features'][:,projection];upstream=np.isfinite(D['features'][:,6:24]).all(1);ck('upstream mapped',eq(upstream,np.isfinite(X[:,5:23]).all(1)));ck('3datasets structurally absent col1',all(np.isnan(d['features'][:,1]).all() for d in [D]+old));ck('chronological datasets',old[0]['times'][-1]<old[1]['times'][0] and old[1]['times'][-1]<t[0]);configs=cr(W/'outputs/mucum-atualizacao-15h-2026-09-21/previsao-atualizada.csv')
 rows=cr(E/'predictions.csv');groups=defaultdict(list)
 for r in rows:groups[r['phase'],int(r['horizon_h'])].append(r)
 ck('102084rows24groups',len(rows)==102084 and len(groups)==24);ck('unique keys',len({(r['phase'],r['origin'],r['horizon_h']) for r in rows})==102084);ck('48savedmodels',len(list((E/'models').glob('*.joblib')))==48)
 start,end,stop=map(ep,['2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00']);training=[];replays=[];membership=[]
 for h in range(1,13):
  target=np.r_[truth[h:],np.full(h,np.nan)];delta=target-base;eligible=np.isfinite(base)&np.isfinite(target);initial=eligible&(t+h*3600<start);later=eligible&(t>=start)&(t+h*3600<end);extras=[];extras_y=[];extras_target=[];extras_time=[]
  for j,d in enumerate(old):
   y=np.r_[d['truth'][h:],np.full(h,np.nan)];m=np.isfinite(d['base'])&np.isfinite(y);ck(f'old{j}h{h}mask',eq(m,masks[f'old{j}_h{h}']) and not m[-h:].any());ck(f'old{j}h{h}targettime',np.all(d['times'][:-h]+h*3600==d['times'][h:]));extras.append(d['features'][m][:,projection]);extras_y.append((y-d['base'])[m]);extras_target.append(y[m]);extras_time.append(d['times'][m])
  extraX=np.vstack(extras);extraY=np.concatenate(extras_y);extraT=np.concatenate(extras_target);extraTimes=np.concatenate(extras_time)
  for phase,mask,left,right in [('validation',initial,start,end),('test',initial|later,end,stop)]:
   ck(phase+str(h)+' mask',eq(mask,masks[f'{phase}_h{h}']));train=np.flatnonzero(mask);schedule=np.flatnonzero((t>=left)&(t+h*3600<right));apply=np.isfinite(base[schedule]);rr=groups[phase,h];ck(phase+str(h)+'strict cutoff',np.all(t[train]+h*3600<left));ck(phase+str(h)+'schedule',eq(t[schedule],np.array([ep(r['origin']) for r in rr])));ck(phase+str(h)+'target keys',eq(t[schedule]+h*3600,np.array([ep(r['target_time']) for r in rr])));ck(phase+str(h)+'truthbase',eq(target[schedule],np.array([num(r['actual_m']) for r in rr])) and eq(base[schedule],np.array([num(r['base_m']) for r in rr])));ck(phase+str(h)+'upstream population',np.array_equal(upstream[schedule],np.array([r['complete_upstream18']=='True' for r in rr])))
   leaf,loss=ast.literal_eval(configs[h-1]['parameters']);ck('config lead '+str(h),int(float(configs[h-1]['lead_h']))==h and configs[h-1]['model']=='arvores_previsao_chuva')
   expected_params={'max_iter':180,'max_leaf_nodes':leaf,'min_samples_leaf':35,'learning_rate':.055,'l2_regularization':10,'loss':loss,'early_stopping':False,'random_state':57}
   previous_params=None
   for family in F:
    key=f'{phase}-{family}-{h}';added=family==F[1];fy=np.r_[extraY,delta[train]] if added else delta[train];ft=np.r_[extraT,target[train]] if added else target[train];fx=np.vstack([extraX,X[train]]) if added else X[train];times=np.r_[extraTimes,t[train]] if added else t[train];weights=1+2*(abs(fy)>=1)+2*(ft>=9);info=planmap[phase,family,h]
    ck(key+'response',eq(fy,vectors[key+'-response']));ck(key+'target',eq(ft,vectors[key+'-target']));ck(key+'weights',eq(weights,vectors[key+'-weight']));ck(key+'order/no duplicates',np.all(np.diff(times)>0) and len(np.unique(times))==len(times));ck(key+'finite/allNaNcheck',np.isfinite(fy).all() and np.isfinite(ft).all() and not np.isnan(fx).all(0).any());ck(key+'cutoff',np.all(times+h*3600<left));ck(key+'plan',len(fy)==int(info['n']) and len(train)==int(info['recent_n']) and (len(extraY) if added else 0)==int(info['added_n']) and int(weights.sum())==int(info['weight_sum']) and info['latest_recent_target']==iso((t[train]+h*3600).max()) and info['cutoff_exclusive']==iso(left) and int(info['leaf_nodes'])==leaf and info['loss']==loss)
    if added:ck(key+'recent unchanged appended',eq(fx[len(extraY):],X[train]) and eq(fy[len(extraY):],delta[train]) and eq(weights[len(extraY):],vectors[f'{phase}-{F[0]}-{h}-weight']))
    model=joblib.load(use(E/'models'/f'{key}.joblib'));params=model.get_params();ck(key+'configuration',all(params[k]==v for k,v in expected_params.items()) and model.n_features_in_==119 and model.n_iter_==180)
    if previous_params is not None:ck(key+'same all params',params==previous_params)
    previous_params=params
    pred=np.full(len(schedule),np.nan);pred[apply]=model.predict(X[schedule][apply])+base[schedule][apply];saved=np.array([num(r[family+'_m']) for r in rr]);ck(key+'saved inference EXACT',eq(pred,saved));ck(key+'failures exactly base missing',np.array_equal(np.isnan(pred),~apply))
    replays.append({'phase':phase,'family':family,'horizon_h':h,'scheduled':len(schedule),'applied':int(apply.sum()),'missing_base':int((~apply).sum()),'finite_predictions_with_unknown_truth':int((np.isfinite(pred)&~np.isfinite(target[schedule])).sum()),'exact':True,'max_abs_difference_m':0})
    training.append({'phase':phase,'family':family,'horizon_h':h,'n':len(fy),'recent_n':len(train),'added_n':len(extraY) if added else 0,'weight_sum':int(weights.sum()),'input119_sha256':hashlib.sha256(fx.tobytes()).hexdigest(),'response_sha256':hashlib.sha256(fy.tobytes()).hexdigest(),'weight_sha256':hashlib.sha256(weights.tobytes()).hexdigest(),'first_origin':iso(times.min()),'last_origin':iso(times.max()),'latest_target':iso((times+h*3600).max())})
   membership.append({'phase':phase,'horizon_h':h,'scheduled':len(schedule),'recent_train':len(train),'added2018':len(extraY),'recent_indices_sha256':hashlib.sha256(train.tobytes()).hexdigest()})
  print('Replayed horizon',h,flush=True)
 metrics=[]
 for (phase,h),rr in sorted(groups.items()):
  actual=np.array([num(r['actual_m']) for r in rr]);complete=np.array([r['complete_upstream18']=='True' for r in rr])
  for population in ['full_schedule','complete_upstream18','missing_upstream18']:
   pop=np.ones(len(rr),bool) if population=='full_schedule' else complete if population=='complete_upstream18' else ~complete
   for subset in ['all','level_ge_7m']:
    observed=pop&np.isfinite(actual)&(np.ones(len(rr),bool) if subset=='all' else actual>=7)
    for family in F:
     pred=np.array([num(r[family+'_m']) for r in rr]);paired=observed&np.isfinite(pred);error=pred[paired]-actual[paired];ae=abs(error);nobs=int(observed.sum());n=len(error);hits=int((ae<=.5).sum())
     metrics.append({'phase':phase,'horizon_h':h,'population':population,'subset':subset,'family':family,'scheduled_rows':int(pop.sum()),'missing_truth':int((pop&~np.isfinite(actual)).sum()),'observed_targets':nobs,'pairs':n,'failures':nobs-n,'hits':hits,'paired_hit_fraction':hits/n if n else None,'observed_target_hit_fraction':hits/nobs if nobs else None,'mae_m':float(ae.mean()) if n else None,'bias_m':float(error.mean()) if n else None,'p98_abs_m':float(np.quantile(ae,.98)) if n else None,'max_abs_m':float(ae.max()) if n else None})
 key=lambda r:(r['phase'],int(r['horizon_h']),r['population'],r['subset'],r['family']);saved={key(r):r for r in cr(E/'evaluation.csv')};ck('288metrics48applications',len(saved)==len(metrics)==288 and len(replays)==48)
 for r in metrics:
  s=saved[key(r)];ck('metric '+str(key(r)),all(s[k]==v if isinstance(v,str) else s[k]=='' if v is None else abs(float(s[k])-v)<1e-12 for k,v in r.items()))
 idx={key(r):r for r in metrics};contrasts=[]
 for r in metrics:
  if r['family']!=F[1]:continue
  oldr=idx[(r['phase'],r['horizon_h'],r['population'],r['subset'],F[0])];ck('family common denominator '+str(key(r)),all(r[k]==oldr[k] for k in ['scheduled_rows','missing_truth','observed_targets','pairs','failures']))
  contrasts.append({k:r[k] for k in ['phase','horizon_h','population','subset','observed_targets','pairs','failures']}|{'control_hits':oldr['hits'],'augmented_hits':r['hits'],'delta_hits':r['hits']-oldr['hits'],'control_mae_m':oldr['mae_m'],'augmented_mae_m':r['mae_m'],'control_max_m':oldr['max_abs_m'],'augmented_max_m':r['max_abs_m']})
 for p,h in inputs.items():ck('unchanged '+p,sha(Path(p))==h)
 save('training-reconstruction.csv',training);save('inference-replay.csv',replays);save('membership.csv',membership);save('independent-metrics.csv',metrics);save('contrasts.csv',contrasts);dump('input-hashes.json',inputs)
 dump('verification.json',{'passed':True,'checks_count':len(checks),'checks':checks,'models':48,'exact_inference_applications':48,'scheduled_rows':102084,'metrics':288,'masks':48,'training_vectors':144,'estimator_features':119,'source_features':120,'fit_or_network':False,'limits':['SavedHGB does not independently prove actual optimizer samples/weights; evidence is source+prefit vectors+reconstructed membership+hashes, no refit','All recent evaluation windows already development, not fresh prospective evidence','Computational timestamp/precedence conventions do not certify publication/datum/timezone','No promotion, no98percent claim','First120column failedattempt preserved separately;119projection fixed before completed fit']})
 print('PASS',len(checks),'checks',flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=2):main()
