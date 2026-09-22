"""Audit a sealed Radar issue against its actual training support; never fit."""
import argparse,csv,hashlib,json
from datetime import datetime
from pathlib import Path
import joblib,numpy as np
from threadpoolctl import threadpool_limits
import hydro_prospective_ledger as ledger

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def shift(a,h):
    out=np.full_like(a,np.nan);out[:-h]=a[h:];return out
def value(v):return float(v) if np.isfinite(v) else None

def run(source,out):
    assert not out.exists()
    records=ledger.read_records(ledger.DEFAULT);lookup={r['sha256']:r for r in records}
    result=json.loads((source/'run-result.json').read_text());assert len(result['forecasts'])==1
    issue=lookup[result['forecasts'][0]['receipt_sha256']];p=issue['payload']
    assert issue['kind']=='forecast_issue' and p['model_id']=='radar_arvores_live_candidate'
    hashes={str(source/'run-result.json'):sha(source/'run-result.json'),str(Path(__file__)):sha(Path(__file__))}
    for a in p['model_artifacts']:
        path=Path(a['path']);assert sha(path)==a['sha256'];assert sha(ledger.DEFAULT/a['blob'])==a['sha256'];hashes[str(path)]=a['sha256']
    receipts={lookup[h]['payload'].get('source_path'):lookup[h] for h in p['input_receipts']}
    for name in ('radar-features.npz','telemetria-latencia.npz'):
        path=source/name;r=receipts[str(path)];assert sha(path)==r['payload']['blob_sha256'];hashes[str(path)]=sha(path)
    d=dict(np.load(source/'radar-features.npz'));q=np.load(source/'telemetria-latencia.npz')
    t,X,base,truth=(d[k] for k in ('times','features','base','truth'))
    assert X.shape==(len(t),180) and np.all(np.diff(t)==3600)
    np.testing.assert_array_equal(t,q['times'][::4]);np.testing.assert_array_equal(truth,q['raw:86510000:H'][::4])
    catalog=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922/feature-catalog.csv'
    names=[r['name'] for r in csv.DictReader(catalog.open()) if r['year']=='2021'];assert len(names)==120;hashes[str(catalog)]=sha(catalog)
    groups=('Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas')
    names += [f'{model}:{group}:forecastP{window}' for model in ('gfs_seamless','ecmwf_ifs025','icon_global') for group in groups for window in (3,6,9,12)]
    cutoff=ledger.timestamp(p['training_cutoff']).timestamp();bounds=[];summaries=[];membership={}
    for point in p['points']:
        h=int(point['nominal_lead_h']);target=shift(truth,h)
        np.testing.assert_array_equal(target,shift(q['raw:86510000:H'],h*4)[::4])
        mask=np.isfinite(base)&np.isfinite(target)&np.isfinite(X[:,:24]).all(axis=1)&(t+h*3600<cutoff)
        ix=np.flatnonzero(mask);membership[f'h{h}']=ix;assert len(ix)>=1000
        model=joblib.load(source/'models'/f'radar-{h}.joblib')
        pred=float(model.predict(X[-1:])[0]+base[-1]);assert pred==point['level_m']
        statuses=[]
        for col,name in enumerate(names):
            train=X[ix,col];finite=train[np.isfinite(train)];current=X[-1,col]
            lo=float(finite.min()) if len(finite) else None;hi=float(finite.max()) if len(finite) else None
            status=('current_missing_seen_in_training' if np.isnan(train).any() else 'current_missing_unseen_in_training') if not np.isfinite(current) else 'no_finite_training_support' if not len(finite) else 'below_training_min' if current<lo else 'above_training_max' if current>hi else 'within_univariate_range'
            statuses.append(status)
            bounds.append(dict(nominal_lead_h=h,column=col,name=name,current=value(current),training_rows=len(ix),finite_training_rows=len(finite),missing_training_rows=int(np.isnan(train).sum()),minimum=lo,maximum=hi,status=status))
        delta=target[ix]-base[ix]
        summaries.append(dict(nominal_lead_h=h,actual_lead_h=(ledger.timestamp(point['valid_at'])-ledger.timestamp(issue['recorded_at'])).total_seconds()/3600,
            training_rows=len(ix),cutoff_utc=ledger.timestamp(p['training_cutoff']).isoformat(),cutoff_exclusive=p['training_cutoff'],
            actual_last_training_target=datetime.fromtimestamp(float((t[ix]+h*3600).max()),ledger.TZ).isoformat(),
            anchor_m=float(base[-1]),anchor_training_min=float(base[ix].min()),anchor_training_max=float(base[ix].max()),
            target_training_min=float(target[ix].min()),target_training_max=float(target[ix].max()),delta_training_min=float(delta.min()),delta_training_max=float(delta.max()),
            predicted_delta_m=pred-float(base[-1]),forecast_m=pred,
            inputs_below_training_min=statuses.count('below_training_min'),inputs_above_training_max=statuses.count('above_training_max'),
            missing_inputs_seen_in_training=statuses.count('current_missing_seen_in_training'),missing_inputs_unseen_in_training=statuses.count('current_missing_unseen_in_training'),
            finite_inputs_without_training_support=statuses.count('no_finite_training_support')))
    out.mkdir();save(out/'feature-support.csv',bounds);save(out/'horizon-support.csv',summaries);np.savez_compressed(out/'training-indices.npz',**membership)
    dump(out/'audit.json',dict(issue_sha256=issue['sha256'],issued_at=issue['recorded_at'],reference_at=p['reference_at'],source_sha256=hashes,
        forecasts_reproduced=len(summaries),feature_bounds=len(bounds),fit_performed=False,model_changed=False,goal_achieved=False,
        limits=['Univariate ranges do not prove multivariate support or quantify uncertainty.',
                'A residual model may forecast a level beyond historical target extrema; these are diagnostics, not clipping bounds.',
                'Future forecast inputs differ from archived previous-day weather predictors used in training.',
                'Nominal 13/14 use hour12 settings; no accuracy validation at those horizons.',
                'Gauge datum and timestamp certification remain pending.']))
    for path,digest in hashes.items():assert sha(Path(path))==digest
    dump(out/'artifact-hashes.json',[dict(file=str(f.relative_to(out)),sha256=sha(f)) for f in sorted(out.iterdir()) if f.is_file()])
    print(json.dumps(dict(output=str(out),horizons=len(summaries),bounds=len(bounds),first=summaries[0],last=summaries[-1]),ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    with threadpool_limits(limits=2):run(a.source.resolve(),a.out.resolve())
