"""One predeclared change: flood sample-weight threshold9m to7m."""
import csv,hashlib,importlib.metadata,json
from datetime import datetime,timezone
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
import hydro_radar_anchor_age as evaluation

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
OUT=ROOT/'outputs/experimento-radar-peso-cheia-7m-20260922'
PROTOCOL=ROOT/'docs/radar-flood-weight-7m-protocol.json'
CONTROLS=('profile_A_control','profile_B_control','mixed_profile_candidate')
FAMILY='flood_weight_7m'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def array_sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
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
    X=np.where(assignment[:,None]==0,data['features_A'],data['features_B'])
    base=np.where(assignment==0,data['base_A'],data['base_B'])
    meta={(r['phase'],int(r['horizon_h'])):r for r in csv.DictReader((PARENT/'training.csv').open()) if r['family']=='mixed_profile_candidate'}
    old=list(csv.DictReader((PARENT/'predictions.csv').open()));groups={}
    for r in old:groups.setdefault((r['phase'],r['profile'],int(r['nominal_lead_h'])),[]).append(r)
    runtime={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads((PARENT/'experiment.json').read_text())['runtime']
    prepared={};weight_rows=[];saved_weights={}
    for h in range(1,13):
        target=np.full_like(truth,np.nan);target[:-h]=truth[h:]
        for phase in ('validation','test'):
            ix=np.flatnonzero(masks[f'{phase}_h{h}']);delta=target[ix]-base[ix]
            before=1+2*(abs(delta)>=1)+2*(target[ix]>=9)
            after=1+2*(abs(delta)>=1)+2*(target[ix]>=7)
            changed=(target[ix]>=7)&(target[ix]<9)
            assert len(ix)==int(meta[phase,h]['n']) and int(before.sum())==int(meta[phase,h]['weights_sum'])
            np.testing.assert_array_equal(after-before,2*changed.astype(int))
            assert np.isfinite(delta).all() and np.all(t[ix]+h*3600<epoch(meta[phase,h]['cutoff_exclusive']))
            assert int(after.sum()-before.sum())==2*int(changed.sum())
            prepared[phase,h]=(ix,delta,after)
            saved_weights[f'{phase}_h{h}_old']=before;saved_weights[f'{phase}_h{h}_new']=after
            weight_rows.append(dict(phase=phase,horizon_h=h,rows=len(ix),targets_below_7m=int((target[ix]<7).sum()),targets_7_to_9m=int(changed.sum()),targets_ge_9m=int((target[ix]>=9).sum()),
                old_weights_sum=int(before.sum()),new_weights_sum=int(after.sum()),increase=int(after.sum()-before.sum()),old_weights_sha256=array_sha(before),new_weights_sha256=array_sha(after)))
    OUT.mkdir();(OUT/'models').mkdir();(OUT/'code').mkdir()
    (OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    for p in (Path(__file__),Path(evaluation.__file__)):(OUT/'code'/p.name).write_bytes(p.read_bytes())
    np.savez_compressed(OUT/'training-weights.npz',**saved_weights);save(OUT/'weight-plan.csv',weight_rows)
    prepared_hashes={n:sha(OUT/n) for n in ('training-weights.npz','weight-plan.csv')}
    dump(OUT/'pre-fit-manifest.json',dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,prepared_sha256=prepared_hashes,runtime=runtime,planned_models=24,training_started=False))
    predictions=[];training=[];reproduced=[]
    for h in range(1,13):
        for phase in ('validation','test'):
            ix,delta,weights=prepared[phase,h]
            parent=joblib.load(PARENT/'models'/f'{phase}-mixed_profile_candidate-{h}.joblib')
            model=HistGradientBoostingRegressor(**parent.get_params());model.fit(X[ix],delta,sample_weight=weights)
            joblib.dump(model,OUT/'models'/f'{phase}-{h}.joblib')
            training.append({**meta[phase,h],'family':FAMILY,'weights_sum':int(weights.sum()),'old_weights_sum':int(meta[phase,h]['weights_sum']),'flood_weight_threshold_m':7})
            for profile in ('A','B'):
                group=groups[phase,profile,h];origins=np.array([epoch(r['origin']) for r in group]);scheduled=np.searchsorted(t,origins)
                np.testing.assert_array_equal(t[scheduled],origins)
                valid=np.isfinite(data[f'base_{profile}'][scheduled]);apply=scheduled[valid]
                xx=data[f'features_{profile}'][apply];bb=data[f'base_{profile}'][apply]
                for family in CONTROLS:
                    control=joblib.load(PARENT/'models'/f'{phase}-{family}-{h}.joblib');values=control.predict(xx)+bb
                    frozen=np.array([float(r[family+'_m']) for r in group if r[family+'_m']!=''])
                    np.testing.assert_array_equal(values,frozen)
                    reproduced.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,predictions=len(values),maximum_difference_m=0.0))
                values=np.full(len(group),np.nan);values[valid]=model.predict(xx)+bb;assert np.isfinite(values[valid]).all()
                for j,r in enumerate(group):predictions.append({**r,FAMILY+'_m':float(values[j]) if valid[j] else ''})
            print('flood weight completed',phase,h,flush=True)
    predictions.sort(key=lambda r:(r['phase'],r['profile'],r['origin'],int(r['nominal_lead_h'])))
    assert len(predictions)==204168 and len(training)==24 and len(reproduced)==144
    evaluation.FAMILIES=CONTROLS+(FAMILY,);metrics=evaluation.evaluate(predictions);assert len(metrics)==1152
    save(OUT/'predictions.csv',predictions);save(OUT/'evaluation.csv',metrics);save(OUT/'training.csv',training);save(OUT/'control-reproduction.csv',reproduced)
    for path,digest in hashes.items():assert sha(ROOT/path)==digest,path
    for path,digest in prepared_hashes.items():assert sha(OUT/path)==digest
    dump(OUT/'experiment.json',dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,prepared_sha256=prepared_hashes,runtime=runtime,models_fitted=24,scheduled_profile_rows=len(predictions),metrics=len(metrics),independent_test=False,promoted=False,live_issuance=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(dict(output=str(OUT),models=24,metrics=len(metrics))))

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
