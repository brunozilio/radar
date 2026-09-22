"""Registered additive ridge trend plus frozen-configuration residual trees."""
import csv
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

import hydro_radar_anchor_age as evaluation

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
OUT = ROOT/'outputs/experimento-radar-tendencia-linear-20260922'
PROTOCOL = ROOT/'docs/radar-linear-trend-hybrid-protocol.json'
CONTROLS = ('profile_A_control', 'profile_B_control', 'mixed_profile_candidate')
FAMILIES = CONTROLS + ('linear_trend_only', 'linear_trend_hybrid')
INDICES = np.array([6*g+k for g in range(4) for k in range(1,6)])


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, value): p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
def save(p, rows):
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def epoch(s): return datetime.fromisoformat(s).timestamp()


def linear_predict(bundle, X):
    slopes = X[:, bundle['indices']]
    imputed = np.where(np.isfinite(slopes), slopes, bundle['median'])
    return bundle['ridge'].predict(bundle['scaler'].transform(imputed))


def main():
    assert not OUT.exists(), 'Preserve started experiments.'
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol['planned_estimators'] == 48
    for item in json.loads((PARENT/'artifact-hashes.json').read_text()):
        assert sha(PARENT/item['file']) == item['sha256']
    paths = [PROTOCOL, Path(__file__), Path(evaluation.__file__)] + [p for p in PARENT.rglob('*') if p.is_file()]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    data = dict(np.load(PARENT/'prepared-inputs.npz'))
    masks = dict(np.load(PARENT/'training-masks.npz'))
    t, truth, assignment = data['times'], data['truth'], data['assignment']
    mixed = np.where(assignment[:,None]==0, data['features_A'], data['features_B'])
    base = np.where(assignment==0, data['base_A'], data['base_B'])
    rows = list(csv.DictReader((PARENT/'predictions.csv').open()))
    groups = {}
    for phase in ('validation','test'):
        for profile in ('A','B'):
            for h in range(1,13):
                groups[phase,profile,h] = [r for r in rows if r['phase']==phase and r['profile']==profile and int(r['nominal_lead_h'])==h]
    meta = {(r['phase'],int(r['horizon_h'])): r for r in csv.DictReader((PARENT/'training.csv').open()) if r['family']=='mixed_profile_candidate'}
    runtime = {n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime == json.loads((PARENT/'experiment.json').read_text())['runtime']
    OUT.mkdir(); (OUT/'models').mkdir(); (OUT/'code').mkdir()
    (OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    for p in (Path(__file__),Path(evaluation.__file__)):
        (OUT/'code'/p.name).write_bytes(p.read_bytes())
    dump(OUT/'pre-fit-manifest.json', dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(), input_sha256=hashes,
        runtime=runtime, planned_bundles=24, planned_estimators=48, training_started=False, slope_indices=INDICES.tolist()))
    training, reproduced, predictions, coefficients = [], [], [], []
    for h in range(1,13):
        target = np.full_like(truth,np.nan); target[:-h] = truth[h:]
        for phase in ('validation','test'):
            ix = np.flatnonzero(masks[f'{phase}_h{h}'])
            delta = target[ix]-base[ix]
            weights = 1+2*(abs(delta)>=1)+2*(target[ix]>=9)
            info = meta[phase,h]
            assert len(ix)==int(info['n']) and int(weights.sum())==int(info['weights_sum'])
            assert np.all(t[ix]+h*3600 < epoch(info['cutoff_exclusive']))
            slopes = mixed[ix][:,INDICES]
            assert np.isfinite(slopes).all()
            median = np.median(slopes,axis=0)
            scaler = StandardScaler().fit(slopes,sample_weight=weights)
            ridge = Ridge(alpha=1000.0,fit_intercept=True,solver='cholesky')
            ridge.fit(scaler.transform(slopes),delta,sample_weight=weights)
            fitted = ridge.predict(scaler.transform(slopes))
            parent = joblib.load(PARENT/'models'/f'{phase}-mixed_profile_candidate-{h}.joblib')
            tree = HistGradientBoostingRegressor(**parent.get_params())
            tree.fit(mixed[ix],delta-fitted,sample_weight=weights)
            bundle = dict(indices=INDICES,median=median,scaler=scaler,ridge=ridge,tree=tree)
            joblib.dump(bundle,OUT/'models'/f'{phase}-{h}.joblib')
            np.testing.assert_array_equal(linear_predict(bundle,mixed[ix]),fitted)
            # Weighted normal-equation stationarity confirms ridge objective,
            # including the unpenalized intercept; not a validation score.
            z = scaler.transform(slopes)
            residual = fitted-delta
            gradient = z.T@(weights*residual)+1000.0*ridge.coef_
            assert np.max(abs(gradient)) < 1e-7 and abs(weights@residual)<1e-7
            training.append({**info,'family':'linear_trend_hybrid','ridge_alpha':1000.0,'slope_features':20,'tree_features':180,
                'training_slopes_all_finite':True,'normal_equation_max_abs':float(np.max(abs(gradient))),
                'weighted_intercept_residual':float(weights@residual),'ridge_intercept':float(ridge.intercept_)})
            for k,col in enumerate(INDICES):
                coefficients.append(dict(phase=phase,horizon_h=h,input_column=int(col),median=float(median[k]),mean=float(scaler.mean_[k]),scale=float(scaler.scale_[k]),standardized_coefficient=float(ridge.coef_[k]),original_unit_coefficient=float(ridge.coef_[k]/scaler.scale_[k])))
            for profile in ('A','B'):
                group = groups[phase,profile,h]
                origins = np.array([epoch(r['origin']) for r in group])
                scheduled = np.searchsorted(t,origins)
                np.testing.assert_array_equal(t[scheduled],origins)
                valid = np.isfinite(data[f'base_{profile}'][scheduled])
                apply = scheduled[valid]
                X = data[f'features_{profile}'][apply]
                b = data[f'base_{profile}'][apply]
                for family in CONTROLS:
                    control = joblib.load(PARENT/'models'/f'{phase}-{family}-{h}.joblib')
                    values = control.predict(X)+b
                    frozen = np.array([float(r[family+'_m']) for r in group if r[family+'_m']!=''])
                    np.testing.assert_array_equal(values,frozen)
                    reproduced.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,predictions=len(values),maximum_difference_m=0.0))
                linear = linear_predict(bundle,X)
                hybrid = b+linear+tree.predict(X)
                alone = b+linear
                assert np.isfinite(hybrid).all() and np.isfinite(alone).all()
                onlyvals=np.full(len(group),np.nan); hybridvals=onlyvals.copy()
                onlyvals[valid]=alone;hybridvals[valid]=hybrid
                for j,r in enumerate(group):
                    new=dict(r)
                    new['linear_trend_only_m']=float(onlyvals[j]) if valid[j] else ''
                    new['linear_trend_hybrid_m']=float(hybridvals[j]) if valid[j] else ''
                    predictions.append(new)
            print('linear hybrid completed',phase,h,flush=True)
    predictions.sort(key=lambda r:(r['phase'],r['profile'],r['origin'],int(r['nominal_lead_h'])))
    assert len(predictions)==204168 and len(training)==24 and len(reproduced)==144
    evaluation.FAMILIES=FAMILIES
    metrics=evaluation.evaluate(predictions)
    assert len(metrics)==1440
    save(OUT/'predictions.csv',predictions);save(OUT/'evaluation.csv',metrics)
    save(OUT/'training.csv',training);save(OUT/'coefficients.csv',coefficients);save(OUT/'control-reproduction.csv',reproduced)
    for path,digest in hashes.items(): assert sha(ROOT/path)==digest,path
    dump(OUT/'experiment.json',dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,runtime=runtime,
        model_bundles=24,fitted_estimators=48,prediction_rows=len(predictions),metrics=len(metrics),reproduced_control_applications=144,
        independent_test=False,promoted=False,live_issuance=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(dict(output=str(OUT),models=24,metrics=len(metrics))))


if __name__=='__main__':
    with threadpool_limits(limits=2): main()
