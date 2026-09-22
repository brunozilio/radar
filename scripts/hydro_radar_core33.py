"""Predeclared RADAR input ablation crossed with September2023 augmentation."""
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


def key(row):
    return row['phase'], row['origin'], int(row['nominal_lead_h'])


def run():
    ref = ROOT/'outputs/experimento-radar-observado-120-20260921'
    aug = ROOT/'outputs/experimento-radar-historico-2023-20260921'
    native = ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
    new = ROOT/'outputs/radar-matriz-observada-2023-20260921'
    protocol = ROOT/'docs/radar-core33-compatibility-protocol.json'
    spec = json.loads(protocol.read_text())
    columns = np.array(spec['columns_zero_based'])
    np.testing.assert_array_equal(columns,np.r_[np.arange(12),np.arange(24,45)])
    paths = [protocol,verified(native,'features.npz'),verified(new,'features.npz'),
             verified(aug,'predictions.csv'),verified(aug,'training-masks.npz'),
             verified(ref,'training.csv'),verified(aug,'experiment.json'),
             Path(__file__),ROOT/'scripts/hydro_radar_native_missing.py',
             ROOT/'scripts/hydro_radar_reservoir_features.py',ROOT/'scripts/hydro_routing_fit.py',
             ROOT/'scripts/hydro_hourly_forecast.py']
    runtime = {n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads((aug/'experiment.json').read_text())['runtime']
    old = dict(np.load(paths[1])); added = dict(np.load(paths[2]))
    t,F,base,truth,complete = (old[k] for k in ('times','features','base','truth','complete24'))
    nt,NF,nb,ny = (added[k] for k in ('times','features','base','truth'))
    F=F[:,:120]; CF=F[:,columns]; NCF=NF[:,columns]
    assert F.shape==(len(t),120) and NF.shape==(720,120) and CF.shape==(len(t),33)
    assert np.all(np.diff(t)==3600) and np.all(np.diff(nt)==3600) and nt.max()<t.min()
    original=list(csv.DictReader(paths[3].open())); assert len(original)==102084
    lookup={key(r):r for r in original}; assert len(lookup)==len(original)
    frozen_masks=dict(np.load(paths[4]))
    meta={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(paths[5].open())}
    for folder in (ref,aug):
        for phase in ('validation','test'):
            for h in range(1,13): paths.append(verified(folder,f'models/{phase}-{h}.joblib'))
    hashes={str(p.resolve()):sha(p) for p in paths}
    out=ROOT/'outputs/experimento-radar-core33-20260921'
    out.mkdir(exist_ok=False); (out/'models').mkdir()
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    start,end,stop=[epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    boundary=epoch('2023-10-01T00:00:00-03:00')
    predictions,training,reproduction,membership=[],[],[],{}
    for h in range(1,13):
        target=shift(truth,-h); delta=target-base
        newtarget=shift(ny,-h); newdelta=newtarget-nb
        newmask=np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<boundary)
        np.testing.assert_array_equal(newmask,frozen_masks[f'new_h{h}'])
        newidx=np.where(newmask)[0]; membership[f'new_h{h}']=newmask
        masks=training_masks(t,base,target,complete,h,start,end)
        for phase,left,right in [('validation',start,end),('test',end,stop)]:
            train=np.where(masks[phase,'candidate'])[0]; info=meta[phase,h]
            np.testing.assert_array_equal(masks[phase,'candidate'],frozen_masks[f'{phase}_original_h{h}'])
            assert len(train)==int(info['n']) and iso((t[train]+h*3600).max())==info['latest_training_target']
            assert np.all(nt[newidx]+h*3600<epoch(info['cutoff_exclusive']))
            membership[f'{phase}_original_h{h}']=masks[phase,'candidate']
            scheduled=np.where((t>=left)&(t+h*3600<right))[0]
            apply=scheduled[np.isfinite(base[scheduled])]
            values={}
            for folder,family in ((ref,'observed_control'),(aug,'augmented')):
                control=joblib.load(folder/f'models/{phase}-{h}.joblib')
                actual=control.predict(F[apply])+base[apply]
                expected=np.array([float(lookup[phase,iso(t[i]),h][family+'_m']) for i in apply])
                np.testing.assert_array_equal(actual,expected)
                reproduction.append(dict(phase=phase,horizon_h=h,family=family,n=len(apply),max_difference_m=0.0))
            for family,include in [('core_original',False),('core_augmented',True)]:
                model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=int(info['leaf_nodes']),
                    min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=info['loss'],
                    early_stopping=False,random_state=57)
                xfit=np.vstack([NCF[newidx],CF[train]]) if include else CF[train]
                yfit=np.r_[newdelta[newidx],delta[train]] if include else delta[train]
                levels=np.r_[newtarget[newidx],target[train]] if include else target[train]
                weights=1+2*(abs(yfit)>=1)+2*(levels>=9)
                model.fit(xfit,yfit,sample_weight=weights)
                pred=np.full(len(t),np.nan); pred[apply]=model.predict(CF[apply])+base[apply]
                assert np.isfinite(pred[apply]).all()
                values[family]=pred
                joblib.dump(model,out/'models'/f'{phase}-{family}-{h}.joblib')
                training.append(dict(phase=phase,horizon_h=h,family=family,original_n=len(train),
                    added_n=len(newidx) if include else 0,n=len(yfit),features=33,
                    original_targets_ge_7m=int((target[train]>=7).sum()),
                    added_targets_ge_7m=int((newtarget[newidx]>=7).sum()) if include else 0,
                    weight_sum=int(weights.sum()),response_min_m=float(yfit.min()),response_max_m=float(yfit.max()),
                    latest_training_target=info['latest_training_target'],cutoff_exclusive=info['cutoff_exclusive'],
                    leaf_nodes=int(info['leaf_nodes']),loss=info['loss']))
            for i in scheduled:
                r=lookup[phase,iso(t[i]),h]
                assert (float(r['actual_m'])==target[i]) if np.isfinite(target[i]) else not r['actual_m']
                assert bool(r['observed_control_m'])==bool(np.isfinite(values['core_original'][i]))
                row=dict(phase=phase,origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,
                    original_complete24=bool(complete[i]),base_m=float(r['base_m']) if r['base_m'] else None,
                    actual_m=float(r['actual_m']) if r['actual_m'] else None,
                    observed_control_m=float(r['observed_control_m']) if r['observed_control_m'] else None,
                    augmented_m=float(r['augmented_m']) if r['augmented_m'] else None)
                for family,pred in values.items(): row[family+'_m']=float(pred[i]) if np.isfinite(pred[i]) else None
                predictions.append(row)
        print('completed RADAR core33 factorial horizon',h,flush=True)
    predictions.sort(key=key); assert [key(r) for r in predictions]==[key(r) for r in original]
    evaluation=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for population in ('full_schedule','complete24','missing24'):
                    group=[r for r in predictions if r['phase']==phase and r['nominal_lead_h']==h and
                           (population=='full_schedule' or r['original_complete24']==(population=='complete24'))]
                    observed=[r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in spec['families']:
                        pairs=[r for r in observed if r[family+'_m'] is not None]
                        error=np.array([r[family+'_m']-r['actual_m'] for r in pairs]); ae=abs(error)
                        hits=int((ae<=.5).sum())
                        evaluation.append(dict(phase=phase,horizon_h=h,subset=subset,population=population,family=family,
                            scheduled_rows=len(group),observed_targets=len(observed),n=len(ae),failures=len(observed)-len(ae),
                            hits=hits,hit_fraction=hits/len(ae) if len(ae) else None,
                            observed_target_hit_fraction=hits/len(observed) if len(observed) else None,
                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(ae) else None,
                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    save(out/'predictions.csv',predictions);save(out/'evaluation.csv',evaluation)
    save(out/'training.csv',training);save(out/'control-reproduction.csv',reproduction)
    np.savez_compressed(out/'training-masks.npz',**membership)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py': (out/'code'/p.name).write_bytes(p.read_bytes())
    for name,digest in hashes.items(): assert sha(Path(name))==digest
    summary=dict(input_sha256=hashes,runtime=runtime,models_fitted=48,control_models_refitted=0,
        control_models_reproduced=48,rows=len(predictions),identical_availability=True,
        promoted=False,live_issuance=False,goal_achieved=False,limits=spec['limits'])
    (out/'experiment.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p))
        for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'},indent=2),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2): run()
