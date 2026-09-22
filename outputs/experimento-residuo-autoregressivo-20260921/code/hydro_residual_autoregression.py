"""Fixed pre-July ridge model of signed historical flow reconstruction residuals."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from hydro_hourly_forecast import ROOT, BASE, epoch, iso
from hydro_hge_dependencies import weather
from hydro_routing_fit import shift


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, rows):
    with p.open('w') as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def features(anchor, finalized):
    return np.column_stack([anchor, shift(finalized, 1), shift(finalized, 3), shift(finalized, 6)])


def fit(X, y, target_times, cutoff, alpha=1000.):
    mask = np.isfinite(X).all(axis=1) & np.isfinite(y) & (target_times < cutoff)
    if mask.sum() < 100:
        raise ValueError('Insufficient complete pre-cutoff training rows')
    x = X[mask]
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-8] = 1
    z = (x-mean)/scale
    intercept = y[mask].mean()
    beta = np.linalg.solve(z.T@z+alpha*np.eye(x.shape[1]), z.T@(y[mask]-intercept))
    return dict(mean=mean, scale=scale, beta=beta, intercept=intercept), mask


def predict(model, X):
    return (X-model['mean'])/model['scale']@model['beta']+model['intercept']


def corrected_level(base, uncorrected_q, correction, offset, rating):
    if base is None:
        return None, 'baseline_missing'
    if not np.isfinite(correction):
        return base, 'fallback_original_tau6'
    q=uncorrected_q+correction
    if not np.isfinite(q) or q<0:
        return None, 'invalid_candidate_flow'
    return float(rating[0]*(q/1000)**rating[1]+rating[2]+offset), 'candidate_applied'


def run():
    baseline = ROOT/'outputs/experimento-correcao-tau-6h-20260921'
    protocol = ROOT/'docs/residual-autoregression-protocol.json'
    hge_dir = ROOT/'experiments/hge-water-balance'
    pars_path = ROOT/'outputs/mucum-hge-experimental-2026-09-21/parametros.json'
    paths = [protocol, baseline/'predictions.csv', baseline/'modeled-carreiro-inputs.npz',
             BASE/'dados-roteamento.npz', BASE/'telemetria-latencia.npz',
             BASE/'roteamento-vazao-pesos.csv', BASE/'conferencia-balanco.json', pars_path,
             hge_dir/'run.py', hge_dir/'vendor/hydrological_model.py', Path(__file__),
             baseline/'proxy-training.csv', ROOT/'outputs/mucum-hge-experimental-2026-09-21/resultado.json',
             ROOT/'scripts/hydro_hge_dependencies.py',ROOT/'scripts/hydro_routing_fit.py',ROOT/'scripts/hydro_hourly_forecast.py']
    hashes={str(p.resolve()):sha(p) for p in paths}
    cutoff=epoch('2026-07-01T00:00:00-03:00')
    assert all(epoch(r['latest_training_target'])<cutoff for r in csv.DictReader(paths[11].open()))
    assert epoch(json.loads(paths[12].read_text())['calibration']['end_exclusive'])==cutoff
    manifest = json.loads((baseline/'artifact-hashes.json').read_text())
    for p in paths[1:3]:
        assert sha(p) == next(r['sha256'] for r in manifest if r['file'] == p.name)
    d = dict(np.load(paths[3])); z = dict(np.load(paths[4])); times = d['times']
    assert np.all(np.diff(times) == 3600)
    proxy = dict(np.load(paths[2])); np.testing.assert_array_equal(proxy['times'], times)
    spec = importlib.util.spec_from_file_location('hge_residual_ar', hge_dir/'run.py')
    hge = importlib.util.module_from_spec(spec); spec.loader.exec_module(hge)
    pars = next(r['parameters'] for r in json.loads(pars_path.read_text()) if r['pet_mm_day_hypothesis'] == 3)
    pars = np.array([pars[k] for k in hge.NAMES]); area = float(d['area'])
    rating = json.loads(paths[6].read_text())['rating_parameters']
    kernels = list(csv.DictReader(paths[5].open()))
    routed = np.zeros(len(times))
    for source, label, lags in [('julho','14 de Julho',range(1,13)), ('carreiro','Passo Carreiro',range(4,25))]:
        q = d[source]*1000
        if source == 'carreiro': q = np.where(np.isfinite(q), q, proxy['estimated_q_m3_s'][:,0])
        weights = [float(r['weight']) for r in kernels if r['source'] == label]
        assert len(weights)==len(lags) and abs(sum(weights)-1)<1e-6
        subtotal = np.zeros(len(times))
        for lag,w in zip(lags,weights):
            if w != 0: subtotal += w*shift(q,lag)
        routed += subtotal
    members=[]
    for model in ('gfs_seamless','ecmwf_ifs025','icon_global'):
        p = BASE/'nwp-historical-icon.json' if model=='icon_global' else ROOT/f'outputs/mucum-propagacao-2026-09-21/raw/chuva-previsao-historica-{model}.json'
        paths.append(p);hashes[str(p.resolve())]=sha(p)
        values,_=weather(p,times,'precipitation_previous_day1'); members.append(values)
    assert np.all(np.isfinite(members).sum(axis=0)>0)
    mean_rain=np.nanmean(members,axis=0)
    rain=d['amount']+np.maximum(1-d['coverage'],0)*mean_rain
    states,balance=hge.simulate(rain,3.,pars,area,hge.initial_state(pars))
    assert np.max(abs(balance))<1e-8
    exact=np.searchsorted(z['times'],times)
    np.testing.assert_array_equal(z['times'][exact],times)
    finalized=z['raw:86510000:Q'][exact]-routed-states[:,-1]
    anchor=np.full(len(times),np.nan);anchor_h=anchor.copy();anchor_q=anchor.copy()
    for i in range(25,len(times)):
        at=times[i]-900;ai=int(np.searchsorted(z['times'],at))
        if ai==len(z['times']) or z['times'][ai]!=at:continue
        anchor_h[i]=z['raw:86510000:H'][ai];anchor_q[i]=z['raw:86510000:Q'][ai]
        local,err=hge.simulate(mean_rain[i:i+1],3.,pars,area,states[i-1].copy())
        assert np.max(abs(err))<1e-8
        anchor[i]=anchor_q[i]-(.25*(routed[i-1]+states[i-1,-1])+.75*(routed[i]+local[0,-1]))
    X=features(anchor,finalized);cutoff=epoch('2026-07-01T00:00:00-03:00')
    models={};training=[];predictions={}
    for h in range(1,13):
        y=shift(finalized,-h);model,mask=fit(X,y,times+h*3600,cutoff)
        models[str(h)]={k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
        predictions[h]=predict(model,X)
        training.append(dict(horizon_h=h,n=int(mask.sum()),latest_target=iso((times+h*3600)[mask].max()),
                             latest_origin=iso(times[mask].max()),cutoff_exclusive=iso(cutoff)))
    raw=list(csv.DictReader(paths[1].open()));rows=[];max_anchor_delta=0.
    for r in raw:
        i=int(np.searchsorted(times,epoch(r['origin'])));h=int(r['nominal_lead_h'])
        if r['anchor_residual_q_m3_s']:
            delta=abs(anchor[i]-float(r['anchor_residual_q_m3_s']));max_anchor_delta=max(max_anchor_delta,delta)
            assert delta<1e-8
        else: assert not np.isfinite(anchor[i])
        correction=predictions[h][i]
        applied=bool(np.isfinite(X[i]).all() and np.isfinite(correction))
        row=dict(origin=r['origin'],target_time=r['target_time'],nominal_lead_h=h,
                 anchor_at=r['anchor_at'],latest_finalized_feature_at=iso(times[i]-3600),
                 actual_m=float(r['actual_m']) if r['actual_m'] else None,
                 residual_model_applied=applied,correction_q_m3_s=float(correction) if applied else None,
                 fallback_reason='' if applied else 'missing_residual_feature')
        for family in ('reference','julho_levels'):
            base=float(r[family+'_m']) if r[family+'_m'] else None
            uncorrected=float(r[family+'_uncorrected_q_m3_s']) if r[family+'_uncorrected_q_m3_s'] else np.nan
            offset=anchor_h[i]-float(hge.stage(anchor_q[i],rating))
            candidate,status=corrected_level(base,uncorrected,correction if applied else np.nan,offset,rating)
            row[family+'_baseline_m']=base;row[family+'_candidate_m']=candidate;row[family+'_status']=status
        rows.append(row)
    metrics=[]
    for h in range(1,13):
        for subset in ('all','level_ge_7m'):
            group=[r for r in rows if r['nominal_lead_h']==h and r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
            for family in ('reference','julho_levels'):
                common=[r for r in group if all(r[family+'_'+k+'_m'] is not None for k in ('baseline','candidate'))]
                for pop,pool in [('individual',group),('common',common)]:
                    for model in ('baseline','candidate'):
                        paired=[r for r in pool if r[family+'_'+model+'_m'] is not None]
                        errors=np.array([r[family+'_'+model+'_m']-r['actual_m'] for r in paired]);ae=abs(errors)
                        metrics.append(dict(horizon_h=h,subset=subset,family=family,model=model,population=pop,
                                            observed_targets=len(group),n=len(ae),failures=len(group)-len(ae),hits=int((ae<=.5).sum()),
                                            hit_fraction=float((ae<=.5).mean()) if len(ae) else None,
                                            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(errors.mean()) if len(ae) else None,
                                            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None))
    out=ROOT/'outputs/experimento-residuo-autoregressivo-20260921';out.mkdir(exist_ok=False)
    save(out/'predictions.csv',rows);save(out/'evaluation.csv',metrics);save(out/'training.csv',training)
    (out/'models.json').write_text(json.dumps(models,indent=2)+'\n')
    np.savez_compressed(out/'residual-series.npz',times=times,anchor_residual=anchor,finalized_residual=finalized,X=X,
                        anchor_h=anchor_h,anchor_q=anchor_q,routed=routed,local_q=states[:,-1])
    (out/'protocol.json').write_bytes(protocol.read_bytes());(out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for p,digest in hashes.items():assert sha(Path(p))==digest
    summary=dict(input_sha256=hashes,rows=len(rows),models_fitted=12,
                 anchor_reproduction_max_error_m3_s=max_anchor_delta,
                 applied_rows=sum(r['residual_model_applied'] for r in rows),
                 fallback_rows=sum(not r['residual_model_applied'] for r in rows),
                 invalid_candidate_flow={f:sum(r[f+'_status']=='invalid_candidate_flow' for r in rows) for f in ('reference','julho_levels')},
                 promoted=False,live_issuance=False,goal_achieved=False,
                 limitations=json.loads(protocol.read_text())['limitations'])
    (out/'experiment.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=2):run()
