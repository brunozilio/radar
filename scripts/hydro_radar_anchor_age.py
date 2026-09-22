"""Append reconstructed anchor measurement age to the frozen mixed-profile design."""
import csv,hashlib,importlib.metadata,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
OUT=ROOT/'outputs/experimento-radar-idade-ancora-20260922'
PROTOCOL=ROOT/'docs/radar-anchor-age-feature-protocol.json'
SOURCES={'A':ROOT/'outputs/mucum-hourly-20260922T000704-0300','B':ROOT/'outputs/mucum-hourly-20260922T010016-0300'}
PARENT_FAMILIES=('profile_A_control','profile_B_control','mixed_profile_candidate')
FAMILIES=PARENT_FAMILIES+('age_mixed_candidate',)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def key(r):return r['phase'],r['profile'],r['origin'],int(r['nominal_lead_h'])
def epoch(s):return datetime.fromisoformat(s).timestamp()
def evaluate(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
    result=[]
    for (phase,profile,h),group in sorted(groups.items()):
        for population in ('full_schedule','complete24','missing24'):
            pop=[r for r in group if population=='full_schedule' or (r['complete24']=='True')==(population=='complete24')]
            for subset in ('all','level_ge_7m'):
                observed=[r for r in pop if r['actual_m']!='' and (subset=='all' or float(r['actual_m'])>=7)]
                for family in FAMILIES:
                    pairs=[r for r in observed if r[family+'_m']!=''];error=np.array([float(r[family+'_m'])-float(r['actual_m']) for r in pairs]);ae=abs(error);hits=int((ae<=.5).sum())
                    result.append(dict(phase=phase,profile=profile,horizon_h=h,population=population,subset=subset,family=family,
                        scheduled_rows=len(pop),missing_truth=sum(r['actual_m']=='' for r in pop),observed_targets=len(observed),pairs=len(pairs),failures=len(observed)-len(pairs),hits=hits,
                        paired_hit_fraction=hits/len(pairs) if pairs else None,observed_target_hit_fraction=hits/len(observed) if observed else None,
                        mae_m=float(ae.mean()) if pairs else None,bias_m=float(error.mean()) if pairs else None,p98_abs_m=float(np.quantile(ae,.98)) if pairs else None,max_abs_m=float(ae.max()) if pairs else None))
    return result

def run():
    assert not OUT.exists()
    for r in json.loads((PARENT/'artifact-hashes.json').read_text()):assert sha(PARENT/r['file'])==r['sha256']
    data=dict(np.load(PARENT/'prepared-inputs.npz'));masks=dict(np.load(PARENT/'training-masks.npz'));t=data['times'];truth=data['truth'];assignment=data['assignment']
    old=list(csv.DictReader((PARENT/'predictions.csv').open()));assert len(old)==204168
    lookup={key(r):r for r in old};assert len(lookup)==len(old)
    meta={(r['phase'],r['family'],int(r['horizon_h'])):r for r in csv.DictReader((PARENT/'training.csv').open())}
    paths={PROTOCOL,Path(__file__)};paths.update(p for p in PARENT.rglob('*') if p.is_file())
    ages={};features={};age_summary=[];age_trace=[]
    for profile,folder in SOURCES.items():
        source=folder/'history/ana-86510000.npz';manifest=folder/'history/manifest.json';agefile=folder/'idades-fontes.csv'
        assert sha(source)==json.loads(manifest.read_text())['files'][source.name]
        z=dict(np.load(source));row=next(r for r in csv.DictReader(agefile.open()) if r['source']=='86510000');lag=float(row['delay_minutes'])*60
        assert np.all(np.diff(z['times'])>0)
        ix=np.searchsorted(z['times'],t-lag,side='right')-1;safe=np.maximum(ix,0)
        good=(ix>=0)&(t-lag-z['times'][safe]<=900);base=np.where(good,z['level'][safe],np.nan)
        np.testing.assert_array_equal(base,data[f'base_{profile}'])
        age=np.where(np.isfinite(base),(t-z['times'][safe])/60,np.nan)
        np.testing.assert_array_equal(np.isnan(age),np.isnan(base))
        assert np.all(age[np.isfinite(age)]>=lag/60) and np.all(age[np.isfinite(age)]<=lag/60+15)
        ages[profile]=age;features[profile]=np.column_stack([data[f'features_{profile}'],age]);assert features[profile].shape==(len(t),181)
        for v in np.unique(age[np.isfinite(age)]):age_summary.append(dict(profile=profile,age_minutes=float(v),origins=int((age==v).sum())))
        age_summary.append(dict(profile=profile,age_minutes=None,origins=int(np.isnan(age).sum())))
        for i in range(len(t)):
            age_trace.append(dict(profile=profile,origin_epoch=float(t[i]),query_epoch=float(t[i]-lag),source_index=int(ix[i]),selected_source_epoch=float(z['times'][safe[i]]) if ix[i]>=0 else None,
                original_level_m=float(z['level'][safe[i]]) if ix[i]>=0 and np.isfinite(z['level'][safe[i]]) else None,asof_admissible=bool(good[i]),base_m=float(base[i]) if np.isfinite(base[i]) else None,age_minutes=float(age[i]) if np.isfinite(age[i]) else None))
        paths.update((source,manifest,agefile))
    mixed=np.where(assignment[:,None]==0,features['A'],features['B']);mixed_base=np.where(assignment==0,data['base_A'],data['base_B'])
    runtime={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')}
    assert runtime==json.loads((PARENT/'experiment.json').read_text())['runtime']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
    OUT.mkdir();(OUT/'models').mkdir();(OUT/'code').mkdir();(OUT/'code'/Path(__file__).name).write_bytes(Path(__file__).read_bytes());(OUT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    np.savez_compressed(OUT/'age-inputs.npz',age_A=ages['A'],age_B=ages['B']);agehash=sha(OUT/'age-inputs.npz')
    save(OUT/'age-summary.csv',age_summary);save(OUT/'age-trace.csv',age_trace)
    dump(OUT/'pre-fit-manifest.json',dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),input_sha256=hashes,age_inputs_sha256=agehash,
        runtime=runtime,planned_models=24,base_reconstruction_exact=True,age_gate_passed=True,training_started=False))
    start,end,stop=[epoch(s) for s in ('2025-10-01T00:00:00-03:00','2026-07-01T00:00:00-03:00','2026-09-21T00:00:00-03:00')]
    predictions=[];training=[];replay=[]
    for h in range(1,13):
        target=np.full_like(truth,np.nan);target[:-h]=truth[h:]
        for phase,left,right in (('validation',start,end),('test',end,stop)):
            ix=np.flatnonzero(masks[f'{phase}_h{h}']);scheduled=np.flatnonzero((t>=left)&(t+h*3600<right))
            delta=target[ix]-mixed_base[ix];weights=1+2*(abs(delta)>=1)+2*(target[ix]>=9)
            info=meta[phase,'mixed_profile_candidate',h];assert len(ix)==int(info['n']) and int(weights.sum())==int(info['weights_sum'])
            parent=joblib.load(PARENT/'models'/f'{phase}-mixed_profile_candidate-{h}.joblib')
            model=HistGradientBoostingRegressor(**parent.get_params());model.fit(mixed[ix],delta,sample_weight=weights)
            joblib.dump(model,OUT/'models'/f'{phase}-age_mixed_candidate-{h}.joblib')
            training.append({**info,'family':'age_mixed_candidate','features':181})
            for profile in ('A','B'):
                base=data[f'base_{profile}'];apply=scheduled[np.isfinite(base[scheduled])]
                source_rows=[lookup[phase,profile,datetime.fromtimestamp(float(t[i]),datetime.fromisoformat('2026-09-22T00:00:00-03:00').tzinfo).isoformat(),h] for i in scheduled]
                assert [epoch(r['origin']) for r in source_rows]==list(t[scheduled])
                for family in PARENT_FAMILIES:
                    control=joblib.load(PARENT/'models'/f'{phase}-{family}-{h}.joblib')
                    values=control.predict(data[f'features_{profile}'][apply])+base[apply]
                    frozen=np.array([float(r[family+'_m']) for r in source_rows if r[family+'_m']!=''])
                    np.testing.assert_array_equal(values,frozen)
                    replay.append(dict(phase=phase,profile=profile,family=family,horizon_h=h,predictions=len(apply),maximum_difference_m=0.0))
                v=np.full(len(t),np.nan);v[apply]=model.predict(features[profile][apply])+base[apply];assert np.isfinite(v[apply]).all()
                for i,r in zip(scheduled,source_rows):
                    predictions.append({**r,'age_mixed_candidate_m':repr(float(v[i])) if np.isfinite(v[i]) else ''})
            print('anchor age completed',phase,h,flush=True)
    predictions.sort(key=key);assert [key(r) for r in predictions]==[key(r) for r in old]
    metrics=evaluate(predictions);assert len(metrics)==1152 and len(replay)==144
    save(OUT/'predictions.csv',predictions);save(OUT/'evaluation.csv',metrics);save(OUT/'training.csv',training);save(OUT/'control-reproduction.csv',replay)
    for path,digest in hashes.items():assert sha(ROOT/path)==digest,path
    assert sha(OUT/'age-inputs.npz')==agehash
    dump(OUT/'experiment.json',dict(finished_at_utc=datetime.now(timezone.utc).isoformat(),models_fitted=24,controls_reproduced=144,scheduled_profile_rows=len(predictions),metric_rows=len(metrics),
        input_sha256=hashes,age_inputs_sha256=agehash,runtime=runtime,one_additional_feature=True,training_membership_changed=False,weights_changed=False,
        independent_test=False,promoted=False,live_issuance=False,goal_achieved=False))
    dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file()])
    print(json.dumps(dict(output=str(OUT),models=24,metrics=1152,goal_achieved=False)))

if __name__=='__main__':
    with threadpool_limits(limits=2):run()
