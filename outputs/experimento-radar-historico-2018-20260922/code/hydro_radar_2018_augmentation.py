"""Paired recent-only versus 2018 augmentation under an hourly Muçum contract."""
import ast, csv, hashlib, importlib.metadata, json
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT, epoch, iso
from hydro_routing_fit import shift

OUT=ROOT/'outputs/experimento-radar-historico-2018-20260922'
RECENT=ROOT/'outputs/radar-matriz-recente-ancora-horaria-20260922'
OLD=ROOT/'outputs/radar-matrizes-observadas-2018-20260922'
PROTOCOL=ROOT/'docs/radar-2018-hourly-augmentation-protocol.json'
CONFIG=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21/previsao-atualizada.csv'
FAMILIES=('hourly_control','hourly_plus2018')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def number(v): return float(v) if np.isfinite(v) else None


def run():
    # This program starts only after the coordinator verifies the independent
    # preparation audit. Its path is an explicit, hashed prerequisite.
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--recent-audit',type=Path,required=True);args=ap.parse_args()
    assert args.recent_audit.is_file()
    old_audit=ROOT/'outputs/verificacao-radar-matrizes-2018-20260922/manifest.json'
    assert old_audit.is_file()
    paths={PROTOCOL,CONFIG,Path(__file__),args.recent_audit,old_audit,ROOT/'scripts/hydro_routing_fit.py',ROOT/'scripts/hydro_hourly_forecast.py'}
    for folder in (RECENT,OLD):
        manifest=folder/'artifact-hashes.json';paths.add(manifest)
        for item in json.loads(manifest.read_text()):
            path=folder/item['file'];assert sha(path)==item['sha256'];paths.add(path)
    recent=dict(np.load(RECENT/'features.npz'))
    old=[dict(np.load(OLD/f'{label}-features.npz')) for label in ('2018-08-30','2018-09-30')]
    t,X,b,y=(recent[k] for k in ('times','features','base','truth'))
    assert X.shape==(12912,120) and np.isnan(X[:,1]).all()
    assert all(d['features'].shape==(168,120) and np.isnan(d['features'][:,1]).all() for d in old)
    assert old[0]['times'][-1]<old[1]['times'][0]<old[1]['times'][-1]<t[0]
    configs=list(csv.DictReader(CONFIG.open()))
    assert all(int(float(configs[h-1]['lead_h']))==h and configs[h-1]['model']=='arvores_previsao_chuva' for h in range(1,13))
    old_coverage={(r['window'],int(r['horizon_h'])):int(r['pairs']) for r in csv.DictReader((OLD/'target-coverage.csv').open())}
    start,end,stop=[epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    runtime={k:importlib.metadata.version(k) for k in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime['scikit-learn']=='1.9.1'
    hashes={str(p.resolve()):sha(p) for p in sorted(paths)}
    OUT.mkdir(exist_ok=False);(OUT/'models').mkdir()
    masks, vectors, plan, prepared = {},{},[],{}
    for h in range(1,13):
        target=shift(y,-h);delta=target-b;valid=np.isfinite(b)&np.isfinite(target)
        initial=valid&(t+h*3600<start)
        later=valid&(t>=start)&(t+h*3600<end)
        nX,ndelta,ntarget=[],[],[]
        for j,d in enumerate(old):
            ny=shift(d['truth'],-h);nb=d['base'];mask=np.isfinite(nb)&np.isfinite(ny)
            assert not mask[-h:].any()
            label=('2018-08-30','2018-09-30')[j]
            assert int(mask.sum())==old_coverage[label,h]
            masks[f'old{j}_h{h}']=mask
            nX.append(d['features'][mask]);ndelta.append((ny-nb)[mask]);ntarget.append(ny[mask])
        extraX=np.vstack(nX);extraY=np.concatenate(ndelta);extraTarget=np.concatenate(ntarget)
        for phase,mask,left,right in [('validation',initial,start,end),('test',initial|later,end,stop)]:
            masks[f'{phase}_h{h}']=mask
            train=np.flatnonzero(mask);scheduled=np.flatnonzero((t>=left)&(t+h*3600<right));apply=scheduled[np.isfinite(b[scheduled])]
            assert np.all(t[train]+h*3600<left)
            for family in FAMILIES:
                added=family=='hourly_plus2018'
                fy=np.r_[extraY,delta[train]] if added else delta[train]
                ft=np.r_[extraTarget,target[train]] if added else target[train]
                w=1+2*(abs(fy)>=1)+2*(ft>=9)
                key=f'{phase}-{family}-{h}'
                vectors[key+'-response']=fy;vectors[key+'-weight']=w;vectors[key+'-target']=ft
                leaf,loss=ast.literal_eval(configs[h-1]['parameters'])
                plan.append({'phase':phase,'family':family,'horizon_h':h,'recent_n':len(train),'added_n':len(extraY) if added else 0,'n':len(fy),'weight_sum':int(w.sum()),'latest_recent_target':iso((t[train]+h*3600).max()),'cutoff_exclusive':iso(left),'leaf_nodes':leaf,'loss':loss})
            prepared[phase,h]=(train,scheduled,apply,target,extraX)
    np.savez_compressed(OUT/'training-masks.npz',**masks)
    np.savez_compressed(OUT/'training-vectors.npz',**vectors)
    save(OUT/'training-plan.csv',plan)
    sealed={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
    dump(OUT/'pre-fit-manifest.json',{'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':hashes,'prepared_sha256':sealed,'runtime':runtime,'planned_models':48})
    rows=[]
    for h in range(1,13):
        for phase in ('validation','test'):
            train,scheduled,apply,target,extraX=prepared[phase,h]
            predictions={}
            for family in FAMILIES:
                key=f'{phase}-{family}-{h}'
                info=next(r for r in plan if r['phase']==phase and r['family']==family and r['horizon_h']==h)
                fitX=np.vstack([extraX,X[train]]) if family=='hourly_plus2018' else X[train]
                model=HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=info['leaf_nodes'],min_samples_leaf=35,learning_rate=.055,l2_regularization=10,loss=info['loss'],early_stopping=False,random_state=57)
                model.fit(fitX,vectors[key+'-response'],sample_weight=vectors[key+'-weight'])
                pred=np.full(len(t),np.nan);pred[apply]=model.predict(X[apply])+b[apply]
                assert np.isfinite(pred[apply]).all();predictions[family]=pred
                joblib.dump(model,OUT/'models'/f'{key}.joblib')
            for i in scheduled:
                rows.append({'phase':phase,'origin':iso(t[i]),'target_time':iso(t[i]+h*3600),'horizon_h':h,'complete_upstream18':bool(np.isfinite(X[i,6:24]).all()),'base_m':number(b[i]),'actual_m':number(target[i]),**{family+'_m':number(predictions[family][i]) for family in FAMILIES}})
        print('Completed2018 augmentation horizon',h,flush=True)
    assert len(rows)==102084
    save(OUT/'predictions.csv',rows)
    metrics=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for population in ('full_schedule','complete_upstream18','missing_upstream18'):
                group=[r for r in rows if r['phase']==phase and r['horizon_h']==h and (population=='full_schedule' or r['complete_upstream18']==(population=='complete_upstream18'))]
                for subset in ('all','level_ge_7m'):
                    observed=[r for r in group if r['actual_m'] is not None and (subset=='all' or r['actual_m']>=7)]
                    for family in FAMILIES:
                        pairs=[r for r in observed if r[family+'_m'] is not None]
                        err=np.array([r[family+'_m']-r['actual_m'] for r in pairs]);ae=abs(err);hits=int((ae<=.5).sum())
                        metrics.append({'phase':phase,'horizon_h':h,'population':population,'subset':subset,'family':family,'scheduled_rows':len(group),'missing_truth':sum(r['actual_m'] is None for r in group),'observed_targets':len(observed),'pairs':len(pairs),'failures':len(observed)-len(pairs),'hits':hits,'paired_hit_fraction':hits/len(pairs) if pairs else None,'observed_target_hit_fraction':hits/len(observed) if observed else None,'mae_m':float(ae.mean()) if pairs else None,'bias_m':float(err.mean()) if pairs else None,'p98_abs_m':float(np.quantile(ae,.98)) if pairs else None,'max_abs_m':float(ae.max()) if pairs else None})
    save(OUT/'evaluation.csv',metrics)
    for name,digest in hashes.items():assert sha(Path(name))==digest
    for name,digest in sealed.items():assert sha(OUT/name)==digest
    dump(OUT/'experiment.json',{'completed_at_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':hashes,'prepared_sha256':sealed,'runtime':runtime,'models_fitted':48,'rows':len(rows),'metrics':len(metrics),'promoted':False,'goal_achieved':False})
    dump(OUT/'artifact-hashes.json',[{'file':str(p.relative_to(OUT)),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps({'output':str(OUT),'models':48,'rows':len(rows),'metrics':len(metrics)}),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2):run()
