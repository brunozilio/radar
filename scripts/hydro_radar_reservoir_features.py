"""Append fixed historical reservoir level features to the Radar tree model."""
import csv
import importlib.metadata
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from hydro_hourly_forecast import ROOT,epoch,iso
from hydro_routing_fit import shift
from hydro_radar_native_missing import sha,save,training_masks


def verified(folder,name):
    p=folder/name
    manifest=json.loads((folder/'artifact-hashes.json').read_text())
    expected=next(r['sha256'] for r in manifest if r['file']==name)
    if sha(p)!=expected:raise ValueError('Changed frozen input '+str(p))
    return p


def run():
    prior=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
    reservoirs=ROOT/'outputs/experimento-niveis-reservatorios-20260921'
    protocol=ROOT/'docs/radar-reservoir-features-protocol.json'
    paths=[protocol,verified(prior,'features.npz'),verified(prior,'predictions.csv'),verified(prior,'training.csv'),
           verified(prior,'experiment.json'),verified(reservoirs,'additional-features.npz'),
           verified(reservoirs,'experiment.json'),verified(reservoirs,'input-trace.csv'),
           Path(__file__),ROOT/'scripts/hydro_radar_native_missing.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_routing_fit.py']
    runtime={k:importlib.metadata.version(k) for k in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads(paths[4].read_text())['runtime']
    data=dict(np.load(paths[1]));extra=dict(np.load(paths[5]));times=data['times']
    np.testing.assert_array_equal(extra['times'],times)
    base=data['base'];truth=data['truth'];F=data['features'];complete=data['complete24']
    assert F.shape[1]==180 and extra['levels_and_slopes'].shape==(len(times),24)
    full=np.column_stack([F,extra['levels_and_slopes']])
    old=list(csv.DictReader(paths[2].open()))
    lookup={(r['phase'],r['origin'],int(r['nominal_lead_h'])):r for r in old}
    training_reference={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(paths[3].open()) if r['family']=='baseline'}
    for phase in ('validation','test'):
        for h in range(1,13):paths.append(verified(prior,f'models/{phase}-baseline-{h}.joblib'))
    hashes={str(p.resolve()):sha(p) for p in paths}
    start=epoch('2025-10-01T00:00:00-03:00');end=epoch('2026-07-01T00:00:00-03:00');stop=epoch('2026-09-21T00:00:00-03:00')
    out=ROOT/'outputs/experimento-radar-niveis-reservatorios-20260921';out.mkdir(exist_ok=False);(out/'models').mkdir()
    rows=[];training=[];max_control_delta=0.
    for h in range(1,13):
        target=shift(truth,-h);delta=target-base
        masks=training_masks(times,base,target,complete,h,start,end)
        for phase,left,right in [('validation',start,end),('test',end,stop)]:
            train=np.where(masks[phase,'baseline'])[0]
            meta=training_reference[phase,h]
            assert len(train)==int(meta['n']) and iso((times[train]+h*3600).max())==meta['latest_training_target']
            scheduled=np.where((times>=left)&(times+h*3600<right))[0]
            apply=scheduled[np.isfinite(base[scheduled])]
            control=joblib.load(prior/f'models/{phase}-baseline-{h}.joblib')
            baseline=np.full(len(times),np.nan);baseline[apply]=control.predict(F[apply])+base[apply]
            candidate=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=int(meta['leaf_nodes']),min_samples_leaf=35,
                learning_rate=.055,l2_regularization=10,loss=meta['loss'],early_stopping=False,random_state=57)
            weights=1+2*(abs(delta)>=1)+2*(target>=9)
            candidate.fit(full[train],delta[train],sample_weight=weights[train])
            values=np.full(len(times),np.nan);values[apply]=candidate.predict(full[apply])+base[apply]
            assert np.isfinite(values[apply]).all()
            joblib.dump(candidate,out/'models'/f'{phase}-{h}.joblib')
            training.append(dict(phase=phase,horizon_h=h,training_n=len(train),features=full.shape[1],
                                 latest_training_target=meta['latest_training_target'],cutoff_exclusive=meta['cutoff_exclusive'],
                                 leaf_nodes=int(meta['leaf_nodes']),loss=meta['loss'],
                                 training_with_missing_reservoir_input=int((~np.isfinite(extra['levels_and_slopes'][train]).all(axis=1)).sum())))
            for i in scheduled:
                source=lookup[phase,iso(times[i]),h]
                if source['baseline_m']:
                    error=abs(baseline[i]-float(source['baseline_m']));max_control_delta=max(max_control_delta,error);assert error<1e-10
                else:assert not np.isfinite(baseline[i])
                assert (float(source['actual_m'])==target[i]) if source['actual_m'] else not np.isfinite(target[i])
                rows.append(dict(phase=phase,origin=source['origin'],target_time=source['target_time'],nominal_lead_h=h,
                                 original_complete24=bool(complete[i]),missing_reservoir_inputs=int((~np.isfinite(extra['levels_and_slopes'][i])).sum()),
                                 base_m=float(base[i]) if np.isfinite(base[i]) else None,actual_m=float(target[i]) if np.isfinite(target[i]) else None,
                                 baseline_m=float(baseline[i]) if np.isfinite(baseline[i]) else None,
                                 candidate_m=float(values[i]) if np.isfinite(values[i]) else None))
        print('completed Radar reservoir horizon',h,flush=True)
    rows.sort(key=lambda r:(r['phase'],r['origin'],r['nominal_lead_h']))
    assert [(r['phase'],r['origin'],r['nominal_lead_h']) for r in rows]==[(r['phase'],r['origin'],int(r['nominal_lead_h'])) for r in old]
    metrics=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for population in ('full_schedule','complete24','missing24'):
                    group=[r for r in rows if r['phase']==phase and r['nominal_lead_h']==h and (population=='full_schedule' or r['original_complete24']==(population=='complete24'))]
                    observed=[r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in ('baseline','candidate'):
                        pairs=[r for r in observed if r[family+'_m'] is not None]
                        error=np.array([r[family+'_m']-r['actual_m'] for r in pairs]);ae=abs(error)
                        metrics.append(dict(phase=phase,horizon_h=h,subset=subset,population=population,family=family,
                                            scheduled_rows=len(group),observed_targets=len(observed),n=len(ae),failures=len(observed)-len(ae),
                                            hits=int((ae<=.5).sum()),hit_fraction=float((ae<=.5).mean()) if len(ae) else None,
                                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(ae) else None,
                                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    save(out/'predictions.csv',rows);save(out/'evaluation.csv',metrics);save(out/'training.csv',training)
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    np.savez_compressed(out/'features.npz',times=times,features=full,base=base,truth=truth,complete24=complete)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for name,digest in hashes.items():assert sha(Path(name))==digest
    summary=dict(input_sha256=hashes,runtime=runtime,rows=len(rows),models_fitted=24,baseline_models_refitted=0,
                 features=204,maximum_baseline_reproduction_difference_m=max_control_delta,
                 identical_candidate_baseline_availability=all((r['candidate_m'] is None)==(r['baseline_m'] is None) for r in rows),
                 promoted=False,live_issuance=False,goal_achieved=False,limitations=json.loads(protocol.read_text())['limits'])
    (out/'experiment.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'},indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=2):run()
