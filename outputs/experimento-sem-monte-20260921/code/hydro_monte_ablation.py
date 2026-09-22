"""Fixed development ablation of Monte Claro predictors for Julho discharge."""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT, BASE, epoch, iso, ridge_fit, dump
from hydro_hourly_models import upstream_features
from hydro_upstream_audit import predict_many, metrics, savecsv
from hydro_upstream_tree_experiment import partitions
from hydro_routing_fit import shift

FLOW = ROOT/'outputs/experimento-niveis-reservatorios-20260921'
REMOVED = list(range(8, 16))+list(range(61, 69))
FAMILIES = ['level_and_slopes', 'without_monte']


def without_monte(X):
    if X.ndim != 2 or X.shape[1] != 77:
        raise ValueError('Expected the established 77-column feature contract')
    return np.delete(X, REMOVED, axis=1)


def run(out, protocol):
    policy = json.loads(protocol.read_text())
    if (policy['removed_columns'] != REMOVED or policy['families'] != FAMILIES or
        policy['alpha'] != 1000 or policy['leads_h'] != list(range(12))):
        raise ValueError('Unsupported experiment policy')
    paths = [protocol, BASE/'dados-roteamento.npz', BASE/'telemetria-latencia.npz',
             FLOW/'additional-features.npz', FLOW/'frozen-models.json', FLOW/'predictions.csv',
             FLOW/'artifact-hashes.json', FLOW/'experiment.json', Path(__file__),
             ROOT/'scripts/hydro_hourly_forecast.py', ROOT/'scripts/hydro_hourly_models.py',
             ROOT/'scripts/hydro_upstream_audit.py', ROOT/'scripts/hydro_upstream_tree_experiment.py',
             ROOT/'scripts/hydro_routing_fit.py']
    hashes = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest = json.loads(paths[6].read_text())
    for p in paths[3:6]+[paths[7]]:
        assert hashes[str(p.resolve())] == next(r['sha256'] for r in manifest if r['file'] == p.name)
    names = json.loads(paths[7].read_text())['additional_feature_names']
    assert [j+53 for j,n in enumerate(names) if n.startswith('monte:')] == list(range(61,69))
    assert len(names) == 24
    out.mkdir(parents=True, exist_ok=False)
    (out/'protocol.json').write_bytes(protocol.read_bytes())
    d = dict(np.load(paths[1])); z = dict(np.load(paths[2])); extra = dict(np.load(paths[3])); t = d['times']
    np.testing.assert_array_equal(extra['times'], t)
    F = np.column_stack([upstream_features(z,t),extra['levels_and_slopes']]); X = without_monte(F)
    models = json.loads(paths[4].read_text())
    stored = {(int(r['lead_h']),r['phase'],r['origin']):float(r['forecast_m3_s'])
              for r in csv.DictReader(paths[5].open()) if r['source']=='julho' and r['family']=='level_and_slopes'}
    known = z['julho:Q'][np.searchsorted(z['times'],t)]/1000
    threshold = float(np.nanquantile(d['julho'][t<epoch('2025-10-01T00:00:00-03:00')],.95))
    output_models = {}; evaluations = []; predictions = []; training = []; maximum = 0.
    for lead in range(12):
        target = shift(d['julho'],-lead); delta = target-known; idx = partitions(t,target,known,lead)
        for phase, train, apply in [('validation',idx['train'],idx['validation']),('test',idx['pretest'],idx['test'])]:
            cutoff = epoch('2025-10-01T00:00:00-03:00' if phase=='validation' else '2026-07-01T00:00:00-03:00')
            assert np.all(t[train]+lead*3600<cutoff)
            training.append(dict(lead_h=lead,phase=phase,training_n=len(train),evaluation_n=len(apply),
                                 latest_training_target=iso(max(t[train]+lead*3600)),cutoff_exclusive=iso(cutoff)))
            for family in FAMILIES:
                key = f'julho:{lead}:{phase}:{family}'
                if family=='level_and_slopes':
                    model = {k:np.array(v) if isinstance(v,list) else v for k,v in models[key].items()}; A = F
                else:
                    model = ridge_fit(X,delta,train,1000.,1+2*(target>2)); A = X
                output_models[key] = {k:v.tolist() if isinstance(v,np.ndarray) else float(v) for k,v in model.items()}
                pred = np.maximum(known[apply]+predict_many(model,A[apply]),0)
                if family=='level_and_slopes':
                    expected = np.array([stored[lead,phase,iso(t[i])] for i in apply])
                    difference = float(np.max(abs(pred*1000-expected))); maximum = max(maximum,difference)
                    assert difference < 1e-7
                for subset,values in metrics(pred,target[apply],target[apply]>=threshold).items():
                    evaluations.append(dict(source='julho',lead_h=lead,phase=phase,family=family,subset=subset,**values))
                for i,value in zip(apply,pred):
                    predictions.append(dict(source='julho',lead_h=lead,phase=phase,family=family,origin=iso(t[i]),
                                            target_time=iso(t[i]+lead*3600),actual_m3_s=float(target[i]*1000),
                                            forecast_m3_s=float(value*1000),high_flow=bool(target[i]>=threshold)))
        print('julho',lead,'complete',flush=True)
    savecsv(out/'evaluation.csv',evaluations); savecsv(out/'predictions.csv',predictions)
    savecsv(out/'training.csv',training); dump(out/'frozen-models.json',output_models)
    (out/'code').mkdir()
    for p in paths:
        if p.suffix=='.py': (out/'code'/p.name).write_bytes(p.read_bytes())
    for p,digest in hashes.items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
    dump(out/'experiment.json',dict(input_sha256=hashes,models_newly_fitted=24,models_preserved=len(output_models),
                                   removed_columns=REMOVED,features_candidate=61,prediction_rows=len(predictions),
                                   reference_reproduction_max_difference_m3_s=maximum,
                                   rationale='Ablation motivated by previously inspected Monte Claro flow oscillation; all results remain development.',
                                   historical_availability_verified=False,promoted=False,live_issuance=False,goal_achieved=False))
    print(json.dumps({'output':str(out),'prediction_rows':len(predictions),'reference_difference':maximum}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--protocol',default=ROOT/'docs/monte-ablation-protocol.json',type=Path);a=p.parse_args()
    with threadpool_limits(limits=2): run(a.output,a.protocol)
