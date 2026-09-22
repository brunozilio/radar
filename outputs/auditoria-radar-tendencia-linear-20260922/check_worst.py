from pathlib import Path
from datetime import datetime
import csv,json,hashlib
import numpy as np,joblib
from threadpoolctl import threadpool_limits
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'outputs/experimento-radar-tendencia-linear-20260922';B=R/'outputs/experimento-radar-mistura-atrasos-20260922'
rows=list(csv.DictReader((E/'predictions.csv').open()));data=dict(np.load(B/'prepared-inputs.npz'));bundle=joblib.load(E/'models/test-12.joblib');out=[]
with threadpool_limits(limits=2):
 for profile in ('A','B'):
  rr=[r for r in rows if r['phase']=='test' and r['profile']==profile and r['nominal_lead_h']=='12' and r['actual_m'] and r['linear_trend_hybrid_m']]
  worst=max(rr,key=lambda r:abs(float(r['linear_trend_hybrid_m'])-float(r['actual_m'])))
  epoch=datetime.fromisoformat(worst['origin']).timestamp();ix=np.flatnonzero(data['times']==epoch);assert len(ix)==1
  X=data['features_'+profile][ix];slopes=X[:,bundle['indices']];missing=~np.isfinite(slopes);filled=np.where(missing,bundle['median'],slopes)
  contributions=((filled-bundle['scaler'].mean_)/bundle['scaler'].scale_)*bundle['ridge'].coef_;linear=float(contributions.sum()+bundle['ridge'].intercept_);tree=float(bundle['tree'].predict(X)[0]);base=float(worst['base_m']);pred=base+linear+tree
  assert abs(pred-float(worst['linear_trend_hybrid_m']))<1e-12
  out.append(dict(profile=profile,origin=worst['origin'],target_time=worst['target_time'],actual_m=float(worst['actual_m']),base_m=base,linear_component_m=linear,tree_component_m=tree,hybrid_m=pred,abs_error_m=abs(pred-float(worst['actual_m'])),dH1_m_per_nominal_hour=float(X[0,2]),missing_slope_columns=bundle['indices'][missing[0]].tolist(),linear_intercept=float(bundle['ridge'].intercept_),standardized_contributions=contributions[0].tolist(),source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (E/'predictions.csv',B/'prepared-inputs.npz',E/'models/test-12.joblib')}))
(P/'worst-h12-equation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ('source_sha256','standardized_contributions')} for r in out],indent=2))
