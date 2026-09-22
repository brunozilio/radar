"""Offline training and chronological holdout evaluation; no provider writes."""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from hydro_encantado import ROOT, MODEL_CONFIGS, feature_names, features, read_levels, sample
from hydro_history import stamp

CUTOFF = stamp('2026-09-21T00:00:00-03:00')
VALIDATION = stamp('2026-01-01T00:00:00-03:00')
TEST = stamp('2026-07-01T00:00:00-03:00')


def scores(prediction, actual, anchor):
    errors = np.abs(prediction - actual)
    return {'n': len(actual), 'mae_m': float(errors.mean()),
            'p90_m': float(np.quantile(errors, .9)),
            'persistence_mae_m': float(np.abs(anchor - actual).mean())}


def train(station='encantado'):
    config = MODEL_CONFIGS[station]
    stations = config['codes']
    out = ROOT / f'outputs/{station}-model-v1'
    out.mkdir(parents=True, exist_ok=True)
    historical = ROOT / 'outputs/mucum-propagacao-2026-09-21/raw'
    inputs = []
    if station == 'encantado':
        parts = []
        for path in sorted((out / 'raw').glob('ana-86720000-*.xml')):
            receipt = json.loads(path.with_suffix('.receipt.json').read_text())
            if hashlib.sha256(path.read_bytes()).hexdigest() != receipt['sha256']:
                raise ValueError('Historical receipt hash mismatch')
            parts.append(read_levels(path, stations[0], stamp(receipt['collected_at'])))
            inputs.append(path)
        merged = {t: v for part in parts for t, v in zip(part['times'], part['level'])}
        times = np.array(sorted(merged))
        series = {stations[0]: {'times': times, 'level': np.array([merged[t] for t in times])}}
    else:
        series = {}
    for code in stations:
        if code not in series:
            path = historical / f'normalized-{code}.npz'
            series[code] = dict(np.load(path))
            inputs.append(path)
    origins = np.arange(np.ceil(max(s['times'][0] for s in series.values()) / 3600) * 3600, CUTOFF, 3600)
    # Apply the same availability stress in train, validation and untouched test.
    scenarios = [(0, 0), (1800, 1800), (3600, 3600), (5400, 5400), (0, 5400), (5400, 0)]
    matrices, anchors = zip(*(features(series, origins, delay, stations=stations) for delay in scenarios))
    X, H = np.concatenate(matrices), np.concatenate(anchors)
    clock = np.tile(origins, len(scenarios))
    destination = ROOT / 'model-artifacts' / config['version']
    destination.mkdir(parents=True, exist_ok=True)
    report, artifacts = [], {}
    # Fixed architecture; hyperparameters are not selected using the held-out test.
    def model():
        return HistGradientBoostingRegressor(max_iter=160, max_leaf_nodes=15, min_samples_leaf=35,
                                            learning_rate=.055, l2_regularization=10,
                                            loss='absolute_error', early_stopping=False, random_state=57)
    for lead in range(1, 7):
        truth, _ = sample(series[stations[0]], origins + lead * 3600, max_age=0)
        target = np.tile(truth, len(scenarios))
        valid = np.isfinite(X).all(axis=1) & np.isfinite(target)
        tr = valid & (clock + lead * 3600 < VALIDATION)
        va = valid & (clock >= VALIDATION) & (clock + lead * 3600 < TEST)
        te = valid & (clock >= TEST) & (clock + lead * 3600 < CUTOFF)
        if min(tr.sum(), va.sum(), te.sum()) < 1000:
            raise ValueError('Insufficient independent temporal coverage')
        fitted = model().fit(X[tr], (target - H)[tr])
        validation = scores(fitted.predict(X[va]) + H[va], target[va], H[va])
        fitted = model().fit(X[tr | va], (target - H)[tr | va])
        prediction = fitted.predict(X[te]) + H[te]
        test = scores(prediction, target[te], H[te])
        changing = np.abs(target[te] - H[te]) >= .5
        changing_test = scores(prediction[changing], target[te][changing], H[te][changing]) if changing.any() else None
        row = {'lead_hours': lead, 'validation': validation, 'test': test, 'changing_test': changing_test}
        report.append(row)
        print(json.dumps(row), flush=True)
        final = valid & (clock + lead * 3600 < CUTOFF)
        fitted = model().fit(X[final], (target - H)[final])
        path = destination / f'forecast-{lead}.joblib'
        joblib.dump(fitted, path, compress=3)
        artifacts[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    passed = all(r[phase]['mae_m'] < r[phase]['persistence_mae_m'] for r in report for phase in ['validation', 'test'])
    metadata = {'id': config['version'], 'station': stations[0], 'horizonHours': 6, 'features': feature_names(stations),
                'trainingCutoff': '2026-09-21T00:00:00-03:00', 'validationStart': '2026-01-01',
                'testStart': '2026-07-01', 'validationPassed': passed, 'artifacts': artifacts,
                'levelRange': {code: [float(np.nanmin(s['level'][s['times'] < CUTOFF])),
                                      float(np.nanmax(s['level'][s['times'] < CUTOFF]))] for code, s in series.items()},
                'metrics': report, 'delayScenariosSeconds': scenarios,
                'limitations': ['Retrospective availability stress; historical publication timestamps unknown.',
                                'Repeated delay scenarios are not independent observations.',
                                'No 2023/2024 extreme-flood validation; no guaranteed accuracy.',
                                'Observed levels only; rainfall forecasts and dam operations are not direct inputs.'],
                'inputs': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in inputs}}

    (destination / 'model.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (out / 'validation.json').write_text(json.dumps(metadata, indent=2) + '\n')
    if not passed:
        raise ValueError('Station model did not outperform persistence at every horizon')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--station', choices=MODEL_CONFIGS, default='encantado')
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        train(args.station)
