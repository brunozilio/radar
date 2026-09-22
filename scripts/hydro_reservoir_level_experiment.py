"""Test reservoir levels as upstream-flow predictors on fixed chronological splits.

Historical publication latency is assumed, not observed. No source mutation,
live forecast, storage conversion, anomaly masking or model promotion.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import BASE, ROOT, dump, epoch, iso, ridge_fit
from hydro_hourly_models import upstream_features
from hydro_routing_fit import shift
from hydro_upstream_audit import metrics, predict_many, savecsv
from hydro_upstream_tree_experiment import partitions

PLANTS = {'julho': 'JIUHQJ', 'monte': 'JIUHMC', 'castro': 'JIUHCA'}
FIELDS = ['val_nivelmontante', 'val_niveljusante']
FAMILIES = ['reference', 'level_and_slopes', 'slopes_only']


def prepare_levels(rows, times):
    times = np.asarray(times, dtype=float)
    if len(times) == 0 or (len(times) > 1 and not np.all(np.diff(times) == 3600)):
        raise ValueError('Consecutive nonempty hourly grid required')
    features = []; names = []; trace = []
    for plant, identifier in PLANTS.items():
        selected = {}
        for row in rows:
            if row['id_reservatorio'].strip() != identifier:
                continue
            at = epoch(row['din_instante'])
            if at in selected:
                raise ValueError(f'Duplicate plant/time: {plant} {iso(at)}')
            selected[at] = row
        if not selected:
            raise ValueError('Missing plant '+plant)
        stamps = np.array(sorted(selected)); cutoff = times-3600
        ix = np.searchsorted(stamps, cutoff, side='right')-1
        safe = np.maximum(ix, 0); age = cutoff-stamps[safe]
        usable = (ix >= 0) & (age >= 0) & (age <= 5400)
        for field in FIELDS:
            raw = []
            for at in stamps:
                try:
                    value = float(selected[at][field])
                except (TypeError, ValueError):
                    value = np.nan
                raw.append(value if np.isfinite(value) else np.nan)
            raw = np.array(raw); value = np.where(usable, raw[safe], np.nan)
            features.extend([value, value-shift(value, 1), (value-shift(value, 3))/3, (value-shift(value, 6))/6])
            names.extend([f'{plant}:{field}:{kind}' for kind in ['level', 'change1', 'slope3', 'slope6']])
            for i, origin in enumerate(times):
                trace.append({'plant': plant, 'field': field, 'origin': iso(origin),
                              'assumed_available_before': iso(cutoff[i]),
                              'source_time': iso(stamps[safe[i]]) if ix[i] >= 0 else '',
                              'age_after_delay_minutes': float(age[i]/60) if ix[i] >= 0 else '',
                              'value_m': float(value[i]) if np.isfinite(value[i]) else '',
                              'usable': bool(usable[i] and np.isfinite(value[i]))})
    return np.column_stack(features), names, trace


def run(out, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    if protocol['families'] != FAMILIES or protocol['alpha'] != 1000 or protocol['leads_h'] != list(range(12)):
        raise ValueError('Unsupported protocol')
    manifest_path = ROOT/protocol['source_manifest']
    manifest = json.loads(manifest_path.read_text()); raw = []; paths = []
    for item in manifest:
        path = ROOT/item['path']
        if path.parent != ROOT/'outputs/mucum-propagacao-2026-09-21/raw' or not path.name.startswith('DADOS_HIDROLOGICOS_HO_'):
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Source changed '+str(path))
        with path.open() as f:
            raw.extend(csv.DictReader(f, delimiter=';'))
        paths.append(path)
    if len(paths) != 18:
        raise ValueError('Expected18 monthly source files')
    d = dict(np.load(BASE/'dados-roteamento.npz')); z = dict(np.load(BASE/'telemetria-latencia.npz'))
    t = d['times']; base = upstream_features(z, t)
    levels, names, trace = prepare_levels(raw, t)
    if base.shape[1] != 53 or levels.shape[1] != 24:
        raise ValueError('Unexpected feature shape')
    columns = {f: np.column_stack([base, levels[:, [i for i, n in enumerate(names) if f == 'level_and_slopes' or not n.endswith(':level')]]]) for f in FAMILIES[1:]}
    columns['reference'] = base
    out.mkdir(parents=True, exist_ok=False)
    (out/'protocol.json').write_bytes(protocol_path.read_bytes())
    np.savez_compressed(out/'additional-features.npz', times=t, levels_and_slopes=levels)
    savecsv(out/'input-trace.csv', trace)
    evals = []; predictions = []; models = {}; coverage = []
    code_paths = [Path(__file__), ROOT/'scripts/hydro_hourly_forecast.py', ROOT/'scripts/hydro_hourly_models.py', ROOT/'scripts/hydro_routing_fit.py', ROOT/'scripts/hydro_upstream_audit.py', ROOT/'scripts/hydro_upstream_tree_experiment.py']
    input_paths = paths+[manifest_path, protocol_path, BASE/'dados-roteamento.npz', BASE/'telemetria-latencia.npz']+code_paths
    input_hashes = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}
    for source, key in [('julho', 'julho:Q'), ('carreiro', '86500000:Q')]:
        known = z[key][np.searchsorted(z['times'], t)]/1000
        threshold = float(np.nanquantile(d[source][t < epoch('2025-10-01T00:00:00-03:00')], .95))
        for lead in protocol['leads_h']:
            target = shift(d[source], -lead); delta = target-known; idx = partitions(t, target, known, lead)
            weights = 1+2*(target > 2)
            for phase, train, apply in [('validation', idx['train'], idx['validation']), ('test', idx['pretest'], idx['test'])]:
                boundary = epoch(protocol['splits']['validation_train_targets_before' if phase == 'validation' else 'test_train_targets_before'])
                if np.any(t[train]+lead*3600 >= boundary):
                    raise ValueError('Future target in training')
                coverage.append({'source': source, 'lead_h': lead, 'phase': phase, 'evaluation_rows': len(apply),
                                 'all_extra_predictors_finite': int(np.isfinite(levels[apply]).all(axis=1).sum()),
                                 'any_extra_predictor_missing': int((~np.isfinite(levels[apply])).any(axis=1).sum())})
                for family in FAMILIES:
                    X = columns[family]; model = ridge_fit(X, delta, train, 1000., weights)
                    pred = np.maximum(known[apply]+predict_many(model, X[apply]), 0)
                    models[f'{source}:{lead}:{phase}:{family}'] = {k: v.tolist() if isinstance(v, np.ndarray) else float(v) for k, v in model.items()}
                    for subset, values in metrics(pred, target[apply], target[apply] >= threshold).items():
                        evals.append({'source': source, 'lead_h': lead, 'phase': phase, 'family': family,
                                      'subset': subset, 'training_rows': len(train), 'features': X.shape[1],
                                      'high_flow_threshold_m3_s': threshold*1000, **values})
                    for i, p in zip(apply, pred):
                        predictions.append({'source': source, 'lead_h': lead, 'phase': phase, 'family': family,
                                            'origin': iso(t[i]), 'target_time': iso(t[i]+lead*3600),
                                            'actual_m3_s': float(target[i]*1000), 'forecast_m3_s': float(p*1000),
                                            'high_flow': bool(target[i] >= threshold)})
            print(source, lead, 'complete', flush=True)
    for name, rows in [('evaluation', evals), ('predictions', predictions), ('coverage', coverage)]:
        savecsv(out/f'{name}.csv', rows)
    dump(out/'frozen-models.json', models)
    for path, expected in input_hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Input changed during experiment '+path)
    (out/'code').mkdir()
    for path in code_paths:
        (out/'code'/path.name).write_bytes(path.read_bytes())
    dump(out/'experiment.json', {'input_sha256': input_hashes, 'additional_feature_names': names,
                               'models_preserved': len(models), 'source_rows': len(raw),
                               'status': 'Historical development, fixed splits, no new independent holdout',
                               'historical_availability_verified': False, 'current_inference': False,
                               'promoted': False, 'live_issuance': False, 'goal_achieved': False})
    print(json.dumps({'output': str(out), 'models': len(models)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=ROOT/'docs/reservoir-level-features-protocol.json')
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args.output, args.protocol)
