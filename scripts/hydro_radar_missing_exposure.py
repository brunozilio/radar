"""Training-only Carreiro block masking with immutable samples and controls."""
import csv, hashlib, importlib.metadata, json
from datetime import datetime, timezone
from pathlib import Path
import joblib, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
import hydro_radar_anchor_age as evaluation

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
OUT=ROOT/'outputs/experimento-radar-ausencia-carreiro-20260922'
PROTOCOL=ROOT/'docs/radar-carreiro-missing-exposure-protocol.json'
CONTROLS=('profile_A_control','profile_B_control','mixed_profile_candidate')
FAMILY='carreiro_missing_exposure'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def epoch(s):return datetime.fromisoformat(s).timestamp()

def main():
    assert not OUT.exists()
    assert json.loads(PROTOCOL.read_text())['planned_models']==24
    for item in json.loads((PARENT/'artifact-hashes.json').read_text()):assert sha(PARENT/item['file'])==item['sha256']
    paths=[PROTOCOL,Path(__file__),Path(evaluation.__file__)]+[p for p in PARENT.rglob('*') if p.is_file()]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    data=dict(np.load(PARENT/'prepared-inputs.npz'));masks=dict(np.load(PARENT/'training-masks.npz'))
    t,truth,assignment=data['times'],data['truth'],data['assignment']
    mixed=np.where(assignment[:,None]==0,data['features_A'],data['features_B'])
    base=np.where(assignment==0,data['base_A'],data['base_B'])
    masked=np.random.Generator(np.random.PCG64(58)).random(len(t))<.25
    exposed=mixed.copy();exposed[masked,18:24]=np.nan
    np.testing.assert_array_equal(exposed[~masked],mixed[~masked])
    np.testing.assert_array_equal(exposed[:,:18],mixed[:,:18])
    np.testing.assert_array_equal(exposed[:,24:],mixed[:,24:])
    assert np.isnan(exposed[masked,18:24]).all()
    old=list(csv.DictReader((PARENT/'predictions.csv').open()))
    groups={}
    for r in old:groups.setdefault((r['phase'],r['profile'],int(r['nominal_lead_h'])),[]).append(r)
    meta={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader((PARENT/'training.csv').open()) if r['family']=='mixed_profile_candidate'}
    runtime={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads((PARENT/'experiment.json').read_text())['runtime']
    OUT.mkdir();(OUT/'models').mkdir();(OUT/'code').mkdir()
    (OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    for p in (Path(__file__),Path(evaluation.__file__)):(OUT/'code'/p.name).write_bytes(p.read_bytes())
    np.savez_compressed(OUT/'masking-plan.npz',times=t,masked=masked)
    planhash=sha(OUT/'masking-plan.npz')
    dump(OUT/'pre-fit-manifest.json',dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,runtime=runtime,
        masking_plan_sha256=planhash,selected_timeline_origins=int(masked.sum()),timeline_origins=len(t),models=24,training_started=False))
    predictions=[];training=[];reproduced=[]
    for h in range(1,13):
        target=np.full_like(truth,np.nan);target[:-h]=truth[h:]
        for phase in ('validation','test'):
            ix=np.flatnonzero(masks[f'{phase}_h{h}']);delta=target[ix]-base[ix]
            weights=1+2*(abs(delta)>=1)+2*(target[ix]>=9)
            info=meta[phase,h]
            assert len(ix)==int(info['n']) and int(weights.sum())==int(info['weights_sum'])
            assert np.all(t[ix]+h*3600<epoch(info['cutoff_exclusive']))
            assert np.isfinite(mixed[ix,:24]).all()
            n=int(masked[ix].sum())
            assert int(np.isnan(exposed[ix,18:24]).sum())==6*n
            np.testing.assert_array_equal(exposed[ix][~masked[ix]],mixed[ix][~masked[ix]])
            parent=joblib.load(PARENT/'models'/f'{phase}-mixed_profile_candidate-{h}.joblib')
            model=HistGradientBoostingRegressor(**parent.get_params())
            model.fit(exposed[ix],delta,sample_weight=weights)
            joblib.dump(model,OUT/'models'/f'{phase}-{h}.joblib')
            training.append({**info,'family':FAMILY,'masked_origins':n,'unmasked_origins':len(ix)-n,'cells_made_missing':6*n,
                'masked_high_targets':int(((target[ix]>=7)&masked[ix]).sum()),'unmasked_high_targets':int(((target[ix]>=7)&~masked[ix]).sum())})
            for profile in ('A','B'):
                group=groups[phase,profile,h];origins=np.array([epoch(r['origin']) for r in group]);scheduled=np.searchsorted(t,origins)
                np.testing.assert_array_equal(t[scheduled],origins)
                valid=np.isfinite(data[f'base_{profile}'][scheduled]);apply=scheduled[valid]
                X=data[f'features_{profile}'][apply];b=data[f'base_{profile}'][apply]
                for family in CONTROLS:
                    control=joblib.load(PARENT/'models'/f'{phase}-{family}-{h}.joblib')
                    result=control.predict(X)+b;frozen=np.array([float(r[family+'_m']) for r in group if r[family+'_m']!=''])
                    np.testing.assert_array_equal(result,frozen)
                    reproduced.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,predictions=len(result),maximum_difference_m=0.0))
                result=model.predict(X)+b;assert np.isfinite(result).all()
                values=np.full(len(group),np.nan);values[valid]=result
                for j,r in enumerate(group):predictions.append({**r,FAMILY+'_m':float(values[j]) if valid[j] else ''})
            print('missing exposure completed',phase,h,flush=True)
    predictions.sort(key=lambda r:(r['phase'],r['profile'],r['origin'],int(r['nominal_lead_h'])))
    assert len(predictions)==204168 and len(training)==24 and len(reproduced)==144
    evaluation.FAMILIES=CONTROLS+(FAMILY,);metrics=evaluation.evaluate(predictions);assert len(metrics)==1152
    save(OUT/'predictions.csv',predictions);save(OUT/'evaluation.csv',metrics);save(OUT/'training.csv',training);save(OUT/'control-reproduction.csv',reproduced)
    for path,digest in hashes.items():assert sha(ROOT/path)==digest,path
    assert sha(OUT/'masking-plan.npz')==planhash
    dump(OUT/'experiment.json',dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,masking_plan_sha256=planhash,runtime=runtime,
        models_fitted=24,scheduled_profile_rows=len(predictions),metrics=len(metrics),independent_test=False,promoted=False,live_issuance=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(dict(output=str(OUT),models=24,metrics=len(metrics))))

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
