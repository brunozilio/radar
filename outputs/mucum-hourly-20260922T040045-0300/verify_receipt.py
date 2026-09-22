"""Verify this completed RADAR cycle, its sealed sources and saved inference."""
import hashlib,json,math,sys
from pathlib import Path
import joblib,numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import hydro_prospective_ledger as ledger
OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    result=json.loads((OUT/'run-result.json').read_text())
    records=ledger.read_records(ledger.DEFAULT);lookup={r['sha256']:r for r in records}
    assert len(result['forecasts'])==1
    f=result['forecasts'][0];record=lookup[f['receipt_sha256']];p=record['payload']
    assert record['kind']=='forecast_issue' and p['model_id']=='radar_arvores_live_candidate'
    assert p['reference_at']==result['reference_at'] and not p.get('manual_revision')
    same=[r for r in records if r['kind']=='forecast_issue' and r['payload']['reference_at']==p['reference_at'] and not r['payload'].get('manual_revision')]
    assert len(same)==1 and same[0]['sha256']==record['sha256']
    assert p['points']==f['points'] and p['last_observed']==result['last_observed']
    cycle=lookup[p['cycle_sha256']];assert cycle['kind']=='cycle_started'
    assert any(r['kind']=='cycle_completed' and r['payload']['cycle_sha256']==cycle['sha256'] for r in records)
    assert not any(r['kind']=='cycle_failed' and r['payload']['cycle_sha256']==cycle['sha256'] for r in records)
    for a in p['model_artifacts']:
        assert sha(Path(a['path']))==a['sha256']
        assert sha(ledger.DEFAULT/a['blob'])==a['sha256']
    issued=ledger.timestamp(record['recorded_at'])
    for h in p['input_receipts']:
        r=lookup[h];v=r['payload'];assert r['kind'] in ('input_receipt','observation_receipt')
        assert ledger.timestamp(r['recorded_at'])<=issued
        assert sha(ledger.DEFAULT/v['blob'])==v['blob_sha256']
        assert sha(Path(v['source_path']))==v['blob_sha256']
    bands=sorted({math.floor((ledger.timestamp(v['valid_at'])-issued).total_seconds()/3600) for v in p['points']})
    assert set(range(1,13))<=set(bands)
    data=dict(np.load(OUT/'radar-features.npz'));assert data['features'].shape[1]==180
    assert data['times'][-1]==ledger.timestamp(p['reference_at']).timestamp()
    for v in p['points']:
        h=int(v['nominal_lead_h']);m=joblib.load(OUT/'models'/f'radar-{h}.joblib')
        predicted=float(m.predict(data['features'][-1:])[0]+data['base'][-1])
        assert predicted==v['level_m']
    collection=json.loads((OUT/'collection-manifest.json').read_text())
    errors=[r for r in collection if 'error' in r]
    assert not any(r['source'] in ('ANA','CERAN','Open-Meteo') for r in errors)
    summary=dict(model=p['model_id'],receipt=record['sha256'],issued_at=record['recorded_at'],reference_at=p['reference_at'],
        last_observed=p['last_observed'],actual_observation_age_at_issue_minutes=(issued-ledger.timestamp(p['last_observed']['last_time'])).total_seconds()/60,
        artifacts_verified=len(p['model_artifacts']),input_receipts_verified=len(p['input_receipts']),real_lead_bands=bands,
        collection_rows=len(collection),collection_errors=len(errors),collection_error_sources={s:sum(r['source']==s for r in errors) for s in {r['source'] for r in errors}},required_collection_errors=0,saved_model_inferences_reproduced=len(p['points']),
        one_regular_issue=True,cycle_completed=True,points=p['points'],goal_achieved=False)
    (OUT/'receipt-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='points'},indent=2))
if __name__=='__main__':
    with threadpool_limits(limits=2):main()
