"""Compare membership and local implementation evidence without model fitting."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,csv,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def fn(path,name):return next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name)
files=[ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_routing_fit.py',ROOT/'scripts/hydro_radar_native_missing.py']
scope={'np':np};exec(compile(ast.Module(body=[fn(files[1],'shift'),fn(files[0],'telemetry_features'),fn(files[2],'training_masks')],type_ignores=[]),'<pure-functions>','exec'),scope)
z=dict(np.load(BASE/'telemetria-latencia.npz'));qt=z['times'];raw={k[4:]:v for k,v in z.items() if k.startswith('raw:')};d={k:v for k,v in z.items() if k!='times' and not k.startswith('raw:')}
t,X,H,truth,phase,_=scope['telemetry_features'](qt,raw,d)
ep=lambda s:datetime.fromisoformat(s).replace(tzinfo=timezone(timedelta(hours=-3))).timestamp()
start=ep('2025-10-01T00:00:00');end=ep('2026-07-01T00:00:00');complete=np.isfinite(X[:,:24]).all(axis=1)
checks=[]
for h in range(1,13):
    target=scope['shift'](truth,-h*4)[phase];valid=np.isfinite(H)&np.isfinite(target)&complete
    tr=np.flatnonzero(valid&(t+h*3600<start));va=np.flatnonzero(valid&(t>=start)&(t+h*3600<end));original=np.r_[tr,va]
    masks=scope['training_masks'](t,H,target,complete,h,start,end);current=np.flatnonzero(masks['test','baseline'])
    delta=target-H;weights=1+2*(abs(delta)>=1)+2*(target>=9)
    checks.append(dict(horizon_h=h,ordered_training_indices_equal=bool(np.array_equal(original,current)),n=len(original),n_tr=len(tr),n_va=len(va),indices_sha256=hashlib.sha256(original.tobytes()).hexdigest(),delta_sha256=hashlib.sha256(delta[original].tobytes()).hexdigest(),weights_sha256=hashlib.sha256(weights[original].tobytes()).hexdigest(),weight_counts={str(v):int((weights[original]==v).sum()) for v in np.unique(weights[original])}))
dump('membership-verification.json',checks)
old=Path('/tmp/radar-hydro-libs/sklearn/ensemble/_hist_gradient_boosting')
new=Path('/tmp/radar-hge-venv/lib/python3.12/site-packages/sklearn/ensemble/_hist_gradient_boosting')
evidence=[];(OUT/'sources').mkdir(exist_ok=True)
for version,base in [('1.6.1',old),('1.9.1',new)]:
    for name in ['binning.py','gradient_boosting.py']:
        p=base/name;s=p.read_text();dest=OUT/'sources'/f'sklearn-{version}-{name}'
        dest.write_bytes(p.read_bytes())
        patterns=['def _find_binning_thresholds','def fit(self, X, y=None','percentile(col_data','method="midpoint"','method="averaged_inverted_cdf"','_weighted_percentile(col_data','X_binned = self._bin_mapper.fit_transform','X, sample_weight=sample_weight']
        evidence.append(dict(version=version,path=str(p),snapshot=str(dest.relative_to(OUT)),sha256=sha(p),excerpts=[dict(line=i+1,text=line.strip()) for i,line in enumerate(s.splitlines()) if any(pat in line for pat in patterns)]))
dump('binning-source-evidence.json',evidence)
param_evidence=[]
for version,base in [('1.6.1',old),('1.9.1',new)]:
    cl=next(x for x in ast.parse((base/'gradient_boosting.py').read_text()).body if isinstance(x,ast.ClassDef) and x.name=='HistGradientBoostingRegressor')
    constructor=next(x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name=='__init__')
    args=constructor.args
    param_evidence.append(dict(version=version,keyword_defaults={a.arg:ast.unparse(d) for a,d in zip(args.kwonlyargs,args.kw_defaults)}))
dump('constructor-defaults.json',param_evidence)
for p in files:
    (OUT/'sources'/p.name).write_bytes(p.read_bytes())
for p in [Path('/tmp/radar-native-missing.log'),ROOT/'scripts/hydro_12h_report.py',ROOT/'scripts/hydro_model.py',BASE/'calculo-estatistico.log']:
    (OUT/'sources'/p.name).write_bytes(p.read_bytes())
dump('source-manifest.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted((OUT/'sources').iterdir())])
print(json.dumps(dict(all_ordered_memberships_equal=all(r['ordered_training_indices_equal'] for r in checks),h1=checks[0],same_constructor_defaults=param_evidence[0]['keyword_defaults']==param_evidence[1]['keyword_defaults']),ensure_ascii=False))
