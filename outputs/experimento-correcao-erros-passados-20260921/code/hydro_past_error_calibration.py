"""Median of already observable original errors; cold start, no recursive correction."""
import argparse,csv,hashlib,json
from collections import deque
from pathlib import Path
import numpy as np
from hydro_hourly_forecast import ROOT,epoch,iso,dump
from hydro_upstream_audit import savecsv
from hydro_verification_metrics import error_metrics

PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'
LABELS=ROOT/'outputs/diagnostico-eventos-proxy-carreiro-20260921'


def past_error_correction(origins,targets,forecast,actual,window_s=86400,delay_s=900,minimum=6):
    arrays=[np.asarray(x,float) for x in [origins,targets,forecast,actual]]
    if len({a.shape for a in arrays})!=1 or arrays[0].ndim!=1:raise ValueError('Mismatched arrays')
    origins,targets,forecast,actual=arrays
    if not np.isfinite(origins).all() or not np.isfinite(targets).all() or np.any(np.diff(origins)<=0) or np.any(np.diff(targets)<=0) or np.any(targets<=origins):raise ValueError('Expected increasing future targets')
    if delay_s<0 or window_s<=delay_s or minimum<1:raise ValueError('Invalid causal calibration settings')
    corrected=forecast.copy();adjustment=np.zeros(len(origins));counts=np.zeros(len(origins),int)
    newest=np.full(len(origins),np.nan);newest_origin=np.full(len(origins),np.nan)
    completed=deque();pointer=0
    for i,at in enumerate(origins):
        while pointer<len(targets) and targets[pointer]+delay_s<=at:
            if origins[pointer]>=at:raise ValueError('Future forecast entered calibration')
            if np.isfinite(forecast[pointer]) and np.isfinite(actual[pointer]):completed.append(pointer)
            pointer+=1
        while completed and targets[completed[0]]<at-window_s:completed.popleft()
        counts[i]=len(completed)
        if completed:
            newest[i]=targets[completed[-1]];newest_origin[i]=origins[completed[-1]]
        if len(completed)>=minimum and np.isfinite(forecast[i]):
            used=np.array(completed)
            adjustment[i]=float(np.median(forecast[used]-actual[used]))
            corrected[i]=forecast[i]-adjustment[i]
    return corrected,adjustment,counts,newest,newest_origin


def evaluate(rows):
    result=[]
    for h in range(1,13):
        for high in [False,True]:
            selected=[r for r in rows if r['nominal_lead_h']==h and r['actual_m'] is not None and (not high or r['actual_m']>=7)]
            for family in ['julho_levels','past_error_median']:
                paired=[r for r in selected if r[family+'_m'] is not None]
                metrics=error_metrics([dict(forecast_m=r[family+'_m'],observed_m=r['actual_m'],valid_at=r['target_time']) for r in paired])
                result.append(dict(nominal_lead_h=h,subset='level_ge_7m' if high else 'all',family=family,observed_targets=len(selected),forecast_failures_with_truth=len(selected)-len(paired),coverage=len(paired)/len(selected) if selected else None,**metrics))
    return result


def run(out,policy_path):
    policy=json.loads(policy_path.read_text())
    if (policy['window_hours'],policy['observation_delay_minutes'],policy['minimum_errors'])!=(24,15,6):raise ValueError('Unsupported protocol')
    paths=[policy_path,PRIOR/'predictions.csv',PRIOR/'artifact-hashes.json',LABELS/'predictions-with-labels.csv',LABELS/'artifact-hashes.json',Path(__file__),ROOT/'scripts/hydro_verification_metrics.py',ROOT/'scripts/hydro_hourly_forecast.py',ROOT/'scripts/hydro_upstream_audit.py']
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    for folder,name in [(PRIOR,'predictions.csv'),(LABELS,'predictions-with-labels.csv')]:
        manifest=json.loads((folder/'artifact-hashes.json').read_text());assert hashes[str((folder/name).resolve())]==manifest[name]
    labels={(r['origin'],r['target_time']):r for r in csv.DictReader(paths[3].open())}
    raw=list(csv.DictReader(paths[1].open()));result=[]
    for horizon in range(1,13):
        group=[r for r in raw if int(r['nominal_lead_h'])==horizon]
        origins=np.array([epoch(r['origin']) for r in group]);targets=np.array([epoch(r['target_time']) for r in group])
        prediction=np.array([float(r['julho_levels_m']) if r['julho_levels_m'] else np.nan for r in group])
        actual=np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in group])
        for r in group:
            label=labels[r['origin'],r['target_time']]
            if r['actual_m']:
                assert label['target_explicitly_approved_and_matching']=='True'
                assert float(r['actual_m'])==float(label['actual_m'])
        corrected,correction,count,last_target,last_origin=past_error_correction(origins,targets,prediction,actual)
        assert np.all(np.isnan(last_target)|(last_target+900<=origins))
        assert np.all(np.isnan(last_origin)|(last_origin<origins))
        for i,r in enumerate(group):
            result.append(dict(origin=r['origin'],target_time=r['target_time'],nominal_lead_h=horizon,actual_m=float(actual[i]) if np.isfinite(actual[i]) else None,julho_levels_m=float(prediction[i]) if np.isfinite(prediction[i]) else None,past_error_median_m=float(corrected[i]) if np.isfinite(corrected[i]) else None,status=r['status'],correction_subtracted_m=float(correction[i]),supporting_errors=int(count[i]),correction_applied=bool(count[i]>=6 and np.isfinite(prediction[i])),latest_supporting_target=iso(last_target[i]) if np.isfinite(last_target[i]) else '',latest_supporting_forecast_origin=iso(last_origin[i]) if np.isfinite(last_origin[i]) else '',observed_cluster_id=labels[r['origin'],r['target_time']]['observed_cluster_id']))
    result.sort(key=lambda r:(r['origin'],r['nominal_lead_h']))
    out.mkdir(parents=True,exist_ok=False);(out/'protocol.json').write_bytes(policy_path.read_bytes())
    savecsv(out/'predictions.csv',result);savecsv(out/'evaluation.csv',evaluate(result))
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py':(out/'code'/p.name).write_bytes(p.read_bytes())
    for name,expected in hashes.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected
    dump(out/'experiment.json',dict(input_sha256=hashes,rows=len(result),corrected_rows=sum(r['correction_applied'] for r in result),negative_corrected_levels=sum(r['past_error_median_m'] is not None and r['past_error_median_m']<0 for r in result),same_forecast_coverage=all((r['julho_levels_m'] is None)==(r['past_error_median_m'] is None) for r in result),hyperparameters_searched=False,historical_observation_availability_verified=False,promoted=False,live_issuance=False,goal_achieved=False))
    print(json.dumps({'output':str(out),'rows':len(result),'corrected_rows':sum(r['correction_applied'] for r in result)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--protocol',type=Path,default=ROOT/'docs/past-error-calibration-protocol.json');a=p.parse_args();run(a.output,a.protocol)
