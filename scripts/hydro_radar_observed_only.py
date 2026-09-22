"""Untuned 120-column RADAR ablation against a frozen 180-column control."""
import csv
import importlib.metadata
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from hydro_hourly_forecast import ROOT,epoch,iso
from hydro_radar_native_missing import sha,save,training_masks
from hydro_radar_reservoir_features import verified
from hydro_routing_fit import shift


def key(r): return r['phase'],r['origin'],int(r['nominal_lead_h'])


def run():
    ref=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
    protocol=ROOT/'docs/radar-observed-only-protocol.json'
    paths=[protocol,verified(ref,'features.npz'),verified(ref,'predictions.csv'),verified(ref,'training.csv'),
        verified(ref,'experiment.json'),Path(__file__),ROOT/'scripts/hydro_radar_native_missing.py',
        ROOT/'scripts/hydro_radar_reservoir_features.py',ROOT/'scripts/hydro_routing_fit.py',ROOT/'scripts/hydro_hourly_forecast.py']
    for phase in ('validation','test'):
        for h in range(1,13):paths.append(verified(ref,f'models/{phase}-candidate-{h}.joblib'))
    runtime={k:importlib.metadata.version(k) for k in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads(paths[4].read_text())['runtime']
    hashes={str(p.resolve()):sha(p) for p in paths}
    data=dict(np.load(paths[1]));t,F,base,truth,complete=(data[k] for k in ('times','features','base','truth','complete24'))
    assert F.shape==(len(t),180) and np.all(np.diff(t)==3600)
    X=F[:,:120]
    original=list(csv.DictReader(paths[2].open()));assert len(original)==102084
    lookup={key(r):r for r in original};assert len(lookup)==len(original)
    metadata={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(paths[3].open()) if r['family']=='candidate'}
    out=ROOT/'outputs/experimento-radar-observado-120-20260921';out.mkdir(exist_ok=False);(out/'models').mkdir()
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    start,end,stop=[epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    predictions=[];training=[];reproduction=[];membership={}
    for h in range(1,13):
        target=shift(truth,-h);delta=target-base
        masks=training_masks(t,base,target,complete,h,start,end)
        for phase,left,right in [('validation',start,end),('test',end,stop)]:
            mask=masks[phase,'candidate'];train=np.flatnonzero(mask);info=metadata[phase,h]
            assert len(train)==int(info['n'])
            assert iso((t[train]+h*3600).max())==info['latest_training_target']
            assert np.all(t[train]+h*3600<epoch(info['cutoff_exclusive']))
            membership[f'{phase}_h{h}']=mask
            scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));apply=scheduled[np.isfinite(base[scheduled])]
            control=joblib.load(ref/f'models/{phase}-candidate-{h}.joblib')
            cp=control.predict(F[apply])+base[apply]
            expected=np.array([float(lookup[phase,iso(t[i]),h]['candidate_m']) for i in apply])
            np.testing.assert_array_equal(cp,expected)
            reproduction.append(dict(phase=phase,horizon_h=h,n=len(apply),max_difference_m=0.0))
            model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=int(info['leaf_nodes']),min_samples_leaf=35,
                learning_rate=.055,l2_regularization=10,loss=info['loss'],early_stopping=False,random_state=57)
            weights=1+2*(abs(delta)>=1)+2*(target>=9)
            model.fit(X[train],delta[train],sample_weight=weights[train])
            pred=np.full(len(t),np.nan);pred[apply]=model.predict(X[apply])+base[apply]
            assert np.isfinite(pred[apply]).all()
            joblib.dump(model,out/'models'/f'{phase}-{h}.joblib')
            training.append(dict(phase=phase,horizon_h=h,n=len(train),features=120,targets_ge_7m=int((target[train]>=7).sum()),
                with_missing_first24=int((~complete[train]).sum()),leaf_nodes=int(info['leaf_nodes']),loss=info['loss'],
                latest_training_target=info['latest_training_target'],cutoff_exclusive=info['cutoff_exclusive']))
            for i in scheduled:
                r=lookup[phase,iso(t[i]),h]
                assert bool(r['candidate_m'])==bool(np.isfinite(pred[i]))
                assert (float(r['actual_m'])==target[i]) if np.isfinite(target[i]) else not r['actual_m']
                predictions.append(dict(phase=phase,origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,
                    original_complete24=bool(complete[i]),base_m=float(r['base_m']) if r['base_m'] else None,
                    actual_m=float(r['actual_m']) if r['actual_m'] else None,
                    native_control_m=float(r['candidate_m']) if r['candidate_m'] else None,
                    observed_only_m=float(pred[i]) if np.isfinite(pred[i]) else None))
        print('completed RADAR observed-only horizon',h,flush=True)
    predictions.sort(key=key);assert [key(r) for r in predictions]==[key(r) for r in original]
    evaluation=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for population in ('full_schedule','complete24','missing24'):
                    group=[r for r in predictions if r['phase']==phase and r['nominal_lead_h']==h and
                        (population=='full_schedule' or r['original_complete24']==(population=='complete24'))]
                    observed=[r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in ('native_control','observed_only'):
                        pairs=[r for r in observed if r[family+'_m'] is not None]
                        errors=np.array([r[family+'_m']-r['actual_m'] for r in pairs]);ae=abs(errors);hits=int((ae<=.5).sum())
                        evaluation.append(dict(phase=phase,horizon_h=h,subset=subset,population=population,family=family,
                            scheduled_rows=len(group),observed_targets=len(observed),n=len(ae),failures=len(observed)-len(ae),hits=hits,
                            hit_fraction=hits/len(ae) if len(ae) else None,observed_target_hit_fraction=hits/len(observed) if len(observed) else None,
                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(errors.mean()) if len(ae) else None,
                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    save(out/'predictions.csv',predictions);save(out/'evaluation.csv',evaluation);save(out/'training.csv',training)
    save(out/'control-reproduction.csv',reproduction);np.savez_compressed(out/'training-masks.npz',**membership)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for p,h in hashes.items():assert sha(Path(p))==h
    result=dict(input_sha256=hashes,runtime=runtime,models_fitted=24,control_models_refitted=0,features=120,
        rows=len(predictions),controls_reproduced_exactly=True,identical_availability=True,old_data_added=False,
        promoted=False,live_issuance=False,goal_achieved=False,limits=json.loads(protocol.read_text())['limits'])
    (out/'experiment.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2):run()
