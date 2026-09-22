"""Radar coverage only. No model training, HGE, collection or operational imports."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
import ast, csv, json, hashlib
import numpy as np
import sklearn
import sklearn.ensemble._hist_gradient_boosting.gradient_boosting as gb

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
TZ=timezone(timedelta(hours=-3))
def epoch(s):return datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def save(name,rr):
    if not rr:return
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)

source_paths=[ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_routing_fit.py',BASE/'telemetria-latencia.npz',BASE/'idades-fontes.csv',BASE/'previsao-atualizada.csv',BASE/'retrospectivas-latencia.csv',Path(gb.__file__)]
sources=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in source_paths]
(OUT/'code').mkdir(exist_ok=True)
for p in source_paths[:3]:(OUT/'code'/p.name).write_bytes(p.read_bytes())
code=(source_paths[0]).read_text();tree=ast.parse(code)
feature_node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='telemetry_features')
shift_tree=ast.parse(source_paths[2].read_text());shift_node=next(x for x in shift_tree.body if isinstance(x,ast.FunctionDef) and x.name=='shift')
scope={'np':np}
exec(compile(ast.Module(body=[shift_node,feature_node],type_ignores=[]),'<extracted-pure-features>','exec'),scope)
# Only the two pure array functions above execute; no operational module imports.
z=dict(np.load(BASE/'telemetria-latencia.npz'));qt=z['times'];raw={k[4:]:v for k,v in z.items() if k.startswith('raw:')};delayed={k:v for k,v in z.items() if k!='times' and not k.startswith('raw:')}
t,X,H,truth,phase,_=scope['telemetry_features'](qt,raw,delayed)
assert np.all(np.diff(t)==3600) and X.shape[1]==120
names=[]
for code in ['86510000','86472000','86472600','86500000']:
    names.extend([code+':H']+[code+':dH'+str(h) for h in [.5,1,2,4,8]])
complete=np.isfinite(X[:,:24]).all(axis=1);own=np.isfinite(X[:,:6]).all(axis=1);aux=np.isfinite(X[:,6:24]).all(axis=1)
start=epoch('2025-10-01T00:00:00');split=epoch('2026-07-01T00:00:00');end=epoch('2026-09-21T00:00:00')
summary=[];excluded=[];byfield=[];events=[];daily=[];expected_keys={};checks=[]
for h in [1,6,12]:
    target=scope['shift'](truth,-h*4)[phase]
    eligible=np.isfinite(H)&np.isfinite(target)
    phases={'train':t+h*3600<start,'validation':(t>=start)&(t+h*3600<split),'test':(t>=split)&(t+h*3600<end),'today':t>=end}
    for pname,period in phases.items():
        available=eligible&period;old=available&complete;excluded_mask=available&~complete
        if pname in ['test','today']:expected_keys[h,pname]={(iso(t[i]),iso(t[i]+h*3600)) for i in np.flatnonzero(old)}
        for label,sub in [('all',np.ones(len(t),dtype=bool)),('high_target_ge_7m',target>=7)]:
            full=available&sub;bad=excluded_mask&sub;ix=np.flatnonzero(bad)
            summary.append(dict(horizon_h=h,phase=pname,subset=label,eligible_base_target=int(full.sum()),original_X24_complete=int((full&complete).sum()),excluded_X24=int(bad.sum()),excluded_pct=100*bad.sum()/max(1,full.sum()),own_mucum_features_missing=int((bad&~own).sum()),aux_features_missing=int((bad&~aux).sum()),aux_only_missing=int((bad&own&~aux).sum()),own_only_missing=int((bad&~own&aux).sum()),both_missing=int((bad&~own&~aux).sum()),max_excluded_target_m=float(target[ix].max()) if len(ix) else '',first_excluded_origin=iso(t[ix[0]]) if len(ix) else '',last_excluded_origin=iso(t[ix[-1]]) if len(ix) else ''))
            for col,name in enumerate(names):byfield.append(dict(horizon_h=h,phase=pname,subset=label,feature_index=col,feature=name,excluded_missing=int((bad&~np.isfinite(X[:,col])).sum())))
            # Consecutive excluded origins, not asserted independent hydrological events.
            chunks=[]
            for i in ix:
                if not chunks or t[i]-t[chunks[-1][-1]]!=3600:chunks.append([])
                chunks[-1].append(i)
            for chunk in chunks:
                missing=sorted({names[j] for i in chunk for j in np.flatnonzero(~np.isfinite(X[i,:24]))})
                events.append(dict(horizon_h=h,phase=pname,subset=label,start_origin=iso(t[chunk[0]]),end_origin=iso(t[chunk[-1]]),n=len(chunk),start_target=iso(t[chunk[0]]+h*3600),end_target=iso(t[chunk[-1]]+h*3600),min_target_m=float(target[chunk].min()),max_target_m=float(target[chunk].max()),missing_features='|'.join(missing)))
        for i in np.flatnonzero(excluded_mask):
            missing=np.flatnonzero(~np.isfinite(X[i,:24]))
            excluded.append(dict(horizon_h=h,phase=pname,origin=iso(t[i]),target_time=iso(t[i]+h*3600),base_m=float(H[i]),target_m=float(target[i]),high_target_ge_7m=bool(target[i]>=7),missing_feature_indices='|'.join(map(str,missing)),missing_features='|'.join(names[j] for j in missing)))
        dates=sorted({iso(t[i])[:10] for i in np.flatnonzero(excluded_mask)})
        for date in dates:
            same=np.array([iso(v).startswith(date) for v in t]);bad=excluded_mask&same
            daily.append(dict(horizon_h=h,phase=pname,date_origin=date,excluded=int(bad.sum()),excluded_high=int((bad&(target>=7)).sum()),max_target_m=float(target[bad].max())))

oldkeys={k:set() for k in expected_keys}
for r in csv.DictReader((BASE/'retrospectivas-latencia.csv').open()):
    h=int(float(r['lead_h']));key=(h,r['phase'])
    if r['model']=='arvores_previsao_chuva' and key in oldkeys:oldkeys[key].add((r['origin'],r['target_time']))
for key,expect in expected_keys.items():
    checks.append(dict(check='original_prediction_membership',horizon_h=key[0],phase=key[1],passed=expect==oldkeys[key],expected=len(expect),preserved=len(oldkeys[key]),missing=len(expect-oldkeys[key]),extra=len(oldkeys[key]-expect)))
sk=Path(gb.__file__).read_text();st=sk.index('This estimator has native support for missing values');en=sk.index('See :ref:',st)
dump('sklearn-evidence.json',dict(version=sklearn.__version__,source=str(Path(gb.__file__)),source_sha256=sha(Path(gb.__file__)),excerpt=sk[st:en].strip(),scope='Installed primary library documentation; not a model execution.'))
source_lines=[]
for p in source_paths[:2]:
    for n,line in enumerate(p.read_text().splitlines(),1):
        if any(v in line for v in ['valid=np.isfinite(H)','No current Muçum','model.predict(features[-1:])','tr=np.where(valid','phase=np.arange(0','apply=np.r_[td,len(times)-1]']):source_lines.append(dict(file=str(p),line=n,text=line))
dump('code-evidence.json',source_lines)
save('coverage-summary.csv',summary);save('excluded-origin-targets.csv',excluded);save('missing-features.csv',byfield);save('excluded-intervals.csv',events);save('daily-exclusions.csv',daily)
dump('verification.json',dict(passed=all(c['passed'] for c in checks),checks=checks,quarter_hour_rows=len(qt),hourly_origins=len(t),telemetry_columns=X.shape[1],weather_columns_not_needed_for_X24_filter=60,current_feature_origin=iso(t[-1]),current_H_finite=bool(np.isfinite(H[-1])),current_X24_complete=bool(complete[-1]),source_sha256=sources,scope='Coverage audit only. No training, HGE execution, network or live changes.'))
dump('artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps(dict(summary_test=[r for r in summary if r['phase']=='test'],checks=checks),ensure_ascii=False,indent=2))
