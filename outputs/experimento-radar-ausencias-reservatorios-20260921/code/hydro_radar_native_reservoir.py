"""Frozen four-family Radar development comparison; no operational mutation."""
import csv
import importlib.metadata
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from hydro_hourly_forecast import ROOT, epoch, iso
from hydro_radar_native_missing import sha, save, training_masks
from hydro_radar_reservoir_features import verified
from hydro_routing_fit import shift

FAMILIES = ('baseline', 'native_only', 'reservoir_only', 'combined')


def key(row):
    return row['phase'], row['origin'], int(row['nominal_lead_h'])


def number(value):
    return float(value) if value else None


def run():
    native = ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
    levels = ROOT/'outputs/experimento-radar-niveis-reservatorios-20260921'
    protocol = ROOT/'docs/radar-native-reservoir-protocol.json'
    assert json.loads(protocol.read_text())['families'] == list(FAMILIES)
    paths = [protocol, verified(levels, 'features.npz'), verified(native, 'predictions.csv'),
             verified(levels, 'predictions.csv'), verified(native, 'training.csv'),
             verified(native, 'experiment.json'), verified(levels, 'experiment.json'),
             Path(__file__), ROOT/'scripts/hydro_radar_native_missing.py',
             ROOT/'scripts/hydro_radar_reservoir_features.py', ROOT/'scripts/hydro_routing_fit.py',
             ROOT/'scripts/hydro_hourly_forecast.py']
    runtime = {k: importlib.metadata.version(k) for k in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime == json.loads(paths[5].read_text())['runtime'] == json.loads(paths[6].read_text())['runtime']
    data = dict(np.load(paths[1]))
    t, F, base, truth, complete = (data[k] for k in ('times','features','base','truth','complete24'))
    assert F.shape == (len(t),204)
    old_native = list(csv.DictReader(paths[2].open()))
    old_levels = list(csv.DictReader(paths[3].open()))
    assert len(old_native) == len(old_levels) == 102084
    assert [key(r) for r in old_native] == [key(r) for r in old_levels]
    lookup = {}
    for a,b in zip(old_native,old_levels):
        for field in ('base_m','actual_m','baseline_m','target_time','original_complete24'):
            assert a[field] == b[field]
        assert bool(a['baseline_m']) == bool(a['candidate_m']) == bool(b['candidate_m'])
        lookup[key(a)] = dict(a, native_only_m=a['candidate_m'], reservoir_only_m=b['candidate_m'])
    meta = {(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(paths[4].open()) if r['family']=='candidate'}
    for phase in ('validation','test'):
        for h in range(1,13):
            paths += [verified(native,f'models/{phase}-baseline-{h}.joblib'),
                      verified(native,f'models/{phase}-candidate-{h}.joblib'),
                      verified(levels,f'models/{phase}-{h}.joblib')]
    hashes = {str(p.resolve()):sha(p) for p in paths}
    out = ROOT/'outputs/experimento-radar-ausencias-reservatorios-20260921'
    out.mkdir(exist_ok=False)
    (out/'models').mkdir()
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    start,end,stop = [epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    predictions,training = [],[]
    for h in range(1,13):
        target = shift(truth,-h)
        delta = target-base
        masks = training_masks(t,base,target,complete,h,start,end)
        for phase,left,right in [('validation',start,end),('test',end,stop)]:
            train = np.where(masks[phase,'candidate'])[0]
            info = meta[phase,h]
            assert len(train) == int(info['n'])
            assert iso((t[train]+h*3600).max()) == info['latest_training_target']
            assert np.all(t[train]+h*3600 < epoch(info['cutoff_exclusive']))
            scheduled = np.where((t>=left)&(t+h*3600<right))[0]
            apply = scheduled[np.isfinite(base[scheduled])]
            model = HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=int(info['leaf_nodes']),
                min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=info['loss'],
                early_stopping=False,random_state=57)
            weights = 1+2*(abs(delta)>=1)+2*(target>=9)
            model.fit(F[train],delta[train],sample_weight=weights[train])
            pred = np.full(len(t),np.nan)
            pred[apply] = model.predict(F[apply])+base[apply]
            assert np.isfinite(pred[apply]).all()
            joblib.dump(model,out/'models'/f'{phase}-{h}.joblib')
            training.append(dict(phase=phase,horizon_h=h,n=len(train),features=F.shape[1],
                                 with_missing_first24=int((~complete[train]).sum()),
                                 with_missing_reservoirs=int((~np.isfinite(F[train,180:]).all(axis=1)).sum()),
                                 targets_ge_7m=int((target[train]>=7).sum()),
                                 latest_training_target=info['latest_training_target'],
                                 cutoff_exclusive=info['cutoff_exclusive'],leaf_nodes=int(info['leaf_nodes']),loss=info['loss']))
            for i in scheduled:
                old = lookup[phase,iso(t[i]),h]
                assert number(old['actual_m']) == float(target[i]) if np.isfinite(target[i]) else not old['actual_m']
                assert bool(old['baseline_m']) == bool(np.isfinite(pred[i]))
                predictions.append(dict(phase=phase,origin=old['origin'],target_time=old['target_time'],nominal_lead_h=h,
                    original_complete24=bool(complete[i]),base_m=number(old['base_m']),actual_m=number(old['actual_m']),
                    baseline_m=number(old['baseline_m']),native_only_m=number(old['native_only_m']),
                    reservoir_only_m=number(old['reservoir_only_m']),combined_m=float(pred[i]) if np.isfinite(pred[i]) else None))
        print('completed Radar combined horizon',h,flush=True)
    predictions.sort(key=key)
    assert [key(r) for r in predictions] == [key(r) for r in old_native]
    evaluation = []
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for population in ('full_schedule','complete24','missing24'):
                    group = [r for r in predictions if r['phase']==phase and r['nominal_lead_h']==h and
                             (population=='full_schedule' or r['original_complete24']==(population=='complete24'))]
                    observed = [r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in FAMILIES:
                        pairs = [r for r in observed if r[family+'_m'] is not None]
                        error = np.array([r[family+'_m']-r['actual_m'] for r in pairs])
                        ae = abs(error)
                        evaluation.append(dict(phase=phase,horizon_h=h,subset=subset,population=population,family=family,
                            scheduled_rows=len(group),observed_targets=len(observed),n=len(ae),failures=len(observed)-len(ae),
                            hits=int((ae<=.5).sum()),hit_fraction=float((ae<=.5).mean()) if len(ae) else None,
                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(ae) else None,
                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    save(out/'predictions.csv',predictions)
    save(out/'evaluation.csv',evaluation)
    save(out/'training.csv',training)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py': (out/'code'/p.name).write_bytes(p.read_bytes())
    for name,digest in hashes.items(): assert sha(Path(name))==digest
    summary = dict(input_sha256=hashes,runtime=runtime,models_fitted=24,control_models_refitted=0,
                   rows=len(predictions),identical_family_availability=True,promoted=False,live_issuance=False,goal_achieved=False,
                   limits=json.loads(protocol.read_text())['limits'])
    (out/'experiment.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'},indent=2),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2): run()
