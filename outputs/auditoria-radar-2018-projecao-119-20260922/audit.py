"""Bounded binning reproduction and48prefit-set projection checks; no model fit."""
from pathlib import Path
import json,csv,hashlib,inspect,traceback,importlib.metadata
import numpy as np
from sklearn.ensemble._hist_gradient_boosting.binning import _find_binning_thresholds,_BinMapper
from threadpoolctl import threadpool_limits
R=Path(__file__).resolve().parent;W=R.parents[1];P=W/'outputs/experimento-radar-historico-2018-20260922';M=W/'outputs/radar-matriz-recente-ancora-horaria-20260922';O=W/'outputs/radar-matrizes-observadas-2018-20260922';checks=[];sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p)]=sha(p);return p
def ck(name,b):assert b,name;checks.append({'check':name,'passed':True})
def save(name,rows):
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def callcase(name,fn):
 try:
  x=fn();return {'case':name,'status':'ok','result':np.asarray(x).tolist() if x is not None else None}
 except Exception as e:return {'case':name,'status':'error','exception_type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
def main():
 src=Path(inspect.getsourcefile(_find_binning_thresholds));use(src);(R/'installed-binning-function.py.txt').write_text(inspect.getsource(_find_binning_thresholds))
 tests=[callcase('thresholds_four_allNaN_positive_weights',lambda:_find_binning_thresholds(np.array([np.nan]*4),255,np.ones(4))),callcase('thresholds_constant_finite_positive_weights',lambda:_find_binning_thresholds(np.ones(4),255,np.ones(4))),callcase('thresholds_mixed_finite_NaN',lambda:_find_binning_thresholds(np.array([1.,np.nan,2.,np.nan]),255,np.ones(4)))]
 tiny=np.column_stack([np.arange(8,dtype=float),np.full(8,np.nan)])
 def binmap(data):
  bm=_BinMapper(n_bins=256,n_threads=1);bm.fit(data,sample_weight=np.ones(len(data)));return bm.n_bins_non_missing_
 tests.extend([callcase('BinMapper8x2_allNaNcolumn',lambda:binmap(tiny)),callcase('BinMapper8x1_projected',lambda:binmap(tiny[:,[0]]))])
 ck('allNaN reproduces ValueError',tests[0]['status']=='error' and tests[0]['exception_type']=='ValueError' and 'window shape cannot be larger' in tests[0]['message'])
 ck('constant control succeeds',tests[1]['status']=='ok' and tests[1]['result']==[]);ck('mixed control succeeds',tests[2]['status']=='ok' and tests[2]['result']==[1.5]);ck('binmapper failure reproduced',tests[3]['status']=='error');ck('binmapper projected succeeds',tests[4]['status']=='ok')
 runtime={k:importlib.metadata.version(k) for k in ['numpy','scikit-learn','scipy','threadpoolctl']}
 (R/'minimal-reproduction.json').write_text(json.dumps({'runtime':runtime,'cases':tests,'scope':'Only threshold/binmapper fits on4or8synthetic rows; zeroHGBmodel fits, no environmental changes.'},indent=2)+'\n')
 pre=json.loads(use(P/'pre-fit-manifest.json').read_text())
 for file,h in pre['prepared_sha256'].items():ck('prefit '+file,sha(P/file)==h)
 masks=dict(np.load(use(P/'training-masks.npz')));vectors=dict(np.load(use(P/'training-vectors.npz')));plan=list(csv.DictReader(use(P/'training-plan.csv').open()));D=dict(np.load(use(M/'features.npz')));old=[dict(np.load(use(O/f'{lab}-features.npz'))) for lab in ['2018-08-30','2018-09-30']];names=json.loads(use(O/'feature-catalog.json').read_text());projection=np.r_[0,np.arange(2,120)];ck('119fixedprojection',len(projection)==119 and set(range(120))-set(projection)=={1});ck('name_of_removed_column',names[1]=='86510000:dH0.5')
 records=[];mapping=[{'projected_index':j,'original_index':int(i),'name':names[i]} for j,i in enumerate(projection)]
 for info in plan:
  phase=info['phase'];h=int(info['horizon_h']);family=info['family'];mask=masks[f'{phase}_h{h}'];X=D['features'][mask];parts=[d['features'][masks[f'old{j}_h{h}']] for j,d in enumerate(old)];extra=np.vstack(parts);full=np.vstack([extra,X]) if family=='hourly_plus2018' else X
  allnan=np.flatnonzero(np.isnan(full).all(0));allnonfinite=np.flatnonzero(~np.isfinite(full).any(0));key=f'{phase}-{family}-{h}';weight=vectors[key+'-weight'];response=vectors[key+'-response'];target=vectors[key+'-target'];projected=full[:,projection]
  ck(key+' onlycolumn1allNaN',allnan.tolist()==[1]);ck(key+' onlycolumn1nonfinite',allnonfinite.tolist()==[1]);ck(key+' nootherallNaNafterprojection',not np.isnan(projected).all(0).any());ck(key+' samplesunchanged',len(full)==int(info['n'])==len(weight)==len(response)==len(target));ck(key+' positiveweights',np.all(weight>0));ck(key+' weightsformula',np.array_equal(weight,1+2*(abs(response)>=1)+2*(target>=9)));ck(key+' upstream18mappedcorrectly',np.array_equal(full[:,6:24],projected[:,5:23],equal_nan=True))
  records.append({'phase':phase,'family':family,'horizon_h':h,'rows':len(full),'all_nan_columns':json.dumps(allnan.tolist()),'all_nonfinite_columns':json.dumps(allnonfinite.tolist()),'projected_columns':projected.shape[1],'projected_all_nan_columns':json.dumps(np.flatnonzero(np.isnan(projected).all(0)).tolist()),'weight_sum':int(weight.sum()),'upstream18_complete_original':int(np.isfinite(full[:,6:24]).all(1).sum()),'upstream18_complete_projected':int(np.isfinite(projected[:,5:23]).all(1).sum())})
 for label,d in [('recent',D),('2018-08-30',old[0]),('2018-09-30',old[1])]:
  ck(label+' removedgloballymissing',np.isnan(d['features'][:,1]).all());ck(label+' originalauxsubsetexact',np.array_equal(np.isfinite(d['features'][:,6:24]).all(1),np.isfinite(d['features'][:,projection][:,5:23]).all(1)))
 ck('48fitsets',len(records)==48);model_files=list((P/'models').rglob('*.joblib'));ck('failedrunhasnomodels',not model_files)
 for p,h in sources.items():ck('source unchanged '+p,sha(Path(p))==h)
 save('48-fitset-missingness.csv',records);save('projection-column-map.csv',mapping)
 result={'passed':True,'check_count':len(checks),'checks':checks,'runtime':runtime,'source_sha256':sources,'fitsets_checked':len(records),'only_column_fully_missing_every_fitset':1,'removed_feature_name':names[1],'projection':projection.tolist(),'original_upstream18_slice':'6:24','projected_upstream18_slice':'5:23','failed_attempt_saved_models':len(model_files),'model_fits_executed_in_audit':0,'limitations':['Local reproducible failure in installed combination, not claim about every sklearn/NumPy version','Only binning on tiny synthetic arrays executed; no full estimator training','Identical projection required at fit/predict and for bothfamilies; feature names and population masks must map original indices','Removing universally absent column addresses observed binning failure but does not certify future fit success or accuracy']}
 (R/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_sha256','projection')},indent=2))
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
