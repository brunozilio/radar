"""Frozen observed120 RADAR control versus predeclared June2024 halfweight sensitivity."""
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
    recent = ROOT/'outputs/radar-matriz-recente-ancora-15min-20260922'
    new = ROOT/'outputs/radar-matriz-observada-junho2024-20260922'
    protocol = ROOT/'docs/radar-june2024-halfweight-protocol.json'
    paths = [protocol, verified(recent, 'features.npz'), verified(ref, 'predictions.csv'),
             verified(ref, 'training.csv'), verified(ref, 'experiment.json'),
             verified(new, '2024-06-15-features.npz'), verified(new, 'preparation.json'),
             Path(__file__), ROOT/'scripts/hydro_radar_native_missing.py',
             ROOT/'scripts/hydro_radar_reservoir_features.py', ROOT/'scripts/hydro_routing_fit.py',
             ROOT/'scripts/hydro_hourly_forecast.py']
    runtime = {n: importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime == json.loads(paths[4].read_text())['runtime']
    old = dict(np.load(paths[1])); added = dict(np.load(paths[5]))
    t, F, base, truth, complete = (old[k] for k in ('times','features','base','truth','complete24'))
    nt, NF, nb, ny = (added[k] for k in ('times','features','base','truth'))
    assert F.shape == (12912,120) and NF.shape == (168,120)
    assert np.all(np.diff(t)==3600) and np.all(np.diff(nt)==3600) and nt.max()<t.min()
    assert not added['complete24'].any() and np.isnan(NF[:,6:12]).all() and np.isnan(NF[:,18:24]).all()
    original = list(csv.DictReader(paths[2].open())); assert len(original)==102084
    lookup = {key(r):r for r in original}; assert len(lookup)==len(original)
    meta = {(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader(paths[3].open())}
    for phase in ('validation','test'):
        for h in range(1,13): paths.append(verified(ref,f'models/{phase}-{h}.joblib'))
    full = ROOT/'outputs/experimento-radar-historico-junho2024-20260922'
    full_prediction = verified(full,'predictions.csv')
    full_masks_path = verified(full,'prefit-masks.npz')
    full_vectors_path = verified(full,'prefit-vectors.npz')
    paths += [full_prediction,full_masks_path,full_vectors_path,verified(full,'prefit-manifest.json')]
    full_rows = list(csv.DictReader(full_prediction.open()))
    full_lookup = {key(r):r for r in full_rows}
    assert set(full_lookup)==set(lookup) and len(full_rows)==len(original)
    full_masks=dict(np.load(full_masks_path));full_vectors=dict(np.load(full_vectors_path))
    hashes = {str(p.resolve()):sha(p) for p in paths}
    out = ROOT/'outputs/experimento-radar-junho2024-meio-peso-20260922'
    out.mkdir(exist_ok=False); (out/'models').mkdir()
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    start,end,stop = [epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    boundary = epoch('2024-06-22T00:00:00-03:00')
    assert nt[0]==epoch('2024-06-15T00:00:00-03:00') and nt[-1]==boundary-3600
    predictions,training,membership = [],[],{}
    reproduction = []
    # Freeze memberships, responses and sample weights before any model is fit.
    prefit_masks, prefit_vectors, prefit_plan = {}, {}, []
    for h in range(1,13):
        target = shift(truth,-h); added_target = shift(ny,-h)
        added_idx = np.flatnonzero(np.isfinite(nb)&np.isfinite(added_target)&(nt+h*3600<boundary))
        masks = training_masks(t,base,target,complete,h,start,end)
        prefit_masks[f'new_h{h}'] = np.isin(np.arange(len(nt)),added_idx)
        for phase in ('validation','test'):
            idx = np.flatnonzero(masks[phase,'candidate'])
            prefit_masks[f'{phase}_original_h{h}'] = masks[phase,'candidate']
            response = np.r_[added_target[added_idx]-nb[added_idx],target[idx]-base[idx]]
            level = np.r_[added_target[added_idx],target[idx]]
            weight = 1+2*(abs(response)>=1)+2*(level>=9)
            weight=weight.astype(float);weight[:len(added_idx)]*=0.5
            prefit_vectors[f'{phase}_h{h}_response'] = response
            prefit_vectors[f'{phase}_h{h}_level'] = level
            prefit_vectors[f'{phase}_h{h}_weight'] = weight
            prefit_plan.append(dict(phase=phase,horizon_h=h,recent_n=len(idx),added_n=len(added_idx),weight_sum=float(weight.sum()),june_weight_sum=float(weight[:len(added_idx)].sum()),recent_weight_sum=float(weight[len(added_idx):].sum()),latest_target=iso((t[idx]+h*3600).max())))
    for k,v in prefit_masks.items():np.testing.assert_array_equal(v,full_masks[k])
    for phase in ('validation','test'):
        for h in range(1,13):
            n=int(prefit_masks[f'new_h{h}'].sum())
            for suffix in ('response','level'):
                k=f'{phase}_h{h}_{suffix}';np.testing.assert_array_equal(prefit_vectors[k],full_vectors[k])
            k=f'{phase}_h{h}_weight';expected=full_vectors[k].astype(float).copy();expected[:n]*=.5
            np.testing.assert_array_equal(prefit_vectors[k],expected)
    np.savez_compressed(out/'prefit-masks.npz',**prefit_masks)
    np.savez_compressed(out/'prefit-vectors.npz',**prefit_vectors)
    save(out/'prefit-plan.csv',prefit_plan)
    from datetime import datetime, timezone
    prefit = dict(created_at=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,
                  artifacts={n:sha(out/n) for n in ['prefit-masks.npz','prefit-vectors.npz','prefit-plan.csv','protocol.json']})
    (out/'prefit-manifest.json').write_text(json.dumps(prefit,indent=2)+'\n')
    for h in range(1,13):
        target = shift(truth,-h); delta = target-base
        newtarget = shift(ny,-h); newdelta = newtarget-nb
        newmask = np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<boundary)
        assert newmask.sum()==168-h
        newidx = np.where(newmask)[0]
        masks = training_masks(t,base,target,complete,h,start,end)
        membership[f'new_h{h}'] = newmask
        for phase,left,right in [('validation',start,end),('test',end,stop)]:
            train = np.where(masks[phase,'candidate'])[0]; info = meta[phase,h]
            assert len(train)==int(info['n'])
            assert iso((t[train]+h*3600).max())==info['latest_training_target']
            assert np.all(nt[newidx]+h*3600<epoch(info['cutoff_exclusive']))
            membership[f'{phase}_original_h{h}'] = masks[phase,'candidate']
            scheduled = np.where((t>=left)&(t+h*3600<right))[0]
            apply = scheduled[np.isfinite(base[scheduled])]
            control = joblib.load(ref/f'models/{phase}-{h}.joblib')
            control_values = control.predict(F[apply])+base[apply]
            frozen_values = np.array([float(lookup[phase,iso(t[i]),h]['observed_only_m']) for i in apply])
            np.testing.assert_array_equal(control_values,frozen_values)
            reproduction.append(dict(phase=phase,horizon_h=h,n=len(apply),max_difference_m=0.0))
            model = HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=int(info['leaf_nodes']),
                min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=info['loss'],
                early_stopping=False,random_state=57)
            xfit = np.vstack([NF[newidx],F[train]])
            yfit = np.r_[newdelta[newidx],delta[train]]
            levels = np.r_[newtarget[newidx],target[train]]
            weights = 1+2*(abs(yfit)>=1)+2*(levels>=9)
            weights=weights.astype(float);weights[:len(newidx)]*=0.5
            np.testing.assert_array_equal(yfit,prefit_vectors[f'{phase}_h{h}_response'])
            np.testing.assert_array_equal(levels,prefit_vectors[f'{phase}_h{h}_level'])
            np.testing.assert_array_equal(weights,prefit_vectors[f'{phase}_h{h}_weight'])
            assert np.isfinite(xfit).any(axis=0).all(), 'All-NaN training column requires explicit protocol revision'
            model.fit(xfit,yfit,sample_weight=weights)
            pred = np.full(len(t),np.nan); pred[apply] = model.predict(F[apply])+base[apply]
            assert np.isfinite(pred[apply]).all()
            joblib.dump(model,out/'models'/f'{phase}-{h}.joblib')
            training.append(dict(phase=phase,horizon_h=h,original_n=len(train),added_n=len(newidx),n=len(yfit),
                features=120,original_targets_ge_7m=int((target[train]>=7).sum()),
                added_targets_ge_7m=int((newtarget[newidx]>=7).sum()),
                original_response_min_m=float(delta[train].min()),original_response_max_m=float(delta[train].max()),
                added_response_min_m=float(newdelta[newidx].min()),added_response_max_m=float(newdelta[newidx].max()),
                combined_response_min_m=float(yfit.min()),combined_response_max_m=float(yfit.max()),
                earliest_added_origin=iso(nt[newidx].min()),latest_added_target=iso((nt[newidx]+h*3600).max()),
                latest_training_target=info['latest_training_target'],cutoff_exclusive=info['cutoff_exclusive'],
                leaf_nodes=int(info['leaf_nodes']),loss=info['loss']))
            for i in scheduled:
                r = lookup[phase,iso(t[i]),h]
                full_r=full_lookup[phase,iso(t[i]),h]
                assert full_r['actual_m']==r['actual_m'] and full_r['base_m']==r['base_m'] and full_r['target_time']==r['target_time']
                assert bool(full_r['augmented_m'])==bool(r['observed_only_m'])
                assert (float(r['actual_m'])==target[i]) if np.isfinite(target[i]) else not r['actual_m']
                assert bool(r['observed_only_m'])==bool(np.isfinite(pred[i]))
                predictions.append(dict(phase=phase,origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,
                    original_complete24=bool(complete[i]),base_m=float(r['base_m']) if r['base_m'] else None,
                    actual_m=float(r['actual_m']) if r['actual_m'] else None,
                    native_control_m=float(r['observed_only_m']) if r['observed_only_m'] else None,
                    full_june_m=float(full_r['augmented_m']) if full_r['augmented_m'] else None,
                    half_june_m=float(pred[i]) if np.isfinite(pred[i]) else None))
        print('completed RADAR June2024 halfweight horizon',h,flush=True)
    predictions.sort(key=key); assert [key(r) for r in predictions]==[key(r) for r in original]
    evaluation = []
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for population in ('full_schedule','complete24','missing24'):
                    group = [r for r in predictions if r['phase']==phase and r['nominal_lead_h']==h and
                             (population=='full_schedule' or r['original_complete24']==(population=='complete24'))]
                    observed = [r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in ('native_control','full_june','half_june'):
                        pairs = [r for r in observed if r[family+'_m'] is not None]
                        error = np.array([r[family+'_m']-r['actual_m'] for r in pairs]); ae = abs(error)
                        hits = int((ae<=.5).sum())
                        evaluation.append(dict(phase=phase,horizon_h=h,subset=subset,population=population,family=family,
                            scheduled_rows=len(group),observed_targets=len(observed),n=len(ae),failures=len(observed)-len(ae),
                            hits=hits,hit_fraction=hits/len(ae) if len(ae) else None,
                            observed_target_hit_fraction=hits/len(observed) if len(observed) else None,
                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(ae) else None,
                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    save(out/'predictions.csv',predictions); save(out/'evaluation.csv',evaluation)
    save(out/'training.csv',training); save(out/'control-reproduction.csv',reproduction)
    np.savez_compressed(out/'training-masks.npz',**membership)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py': (out/'code'/p.name).write_bytes(p.read_bytes())
    for name,digest in hashes.items(): assert sha(Path(name))==digest
    summary = dict(input_sha256=hashes,runtime=runtime,models_fitted=24,control_models_refitted=0,
        rows=len(predictions),identical_availability=True,controls_reproduced_exactly=True,
        promoted=False,live_issuance=False,goal_achieved=False,limits=json.loads(protocol.read_text())['limits'])
    (out/'experiment.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='input_sha256'},indent=2),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2): run()
