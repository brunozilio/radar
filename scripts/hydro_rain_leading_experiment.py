"""Paired retrospective test of observed rain as a leading Muçum signal.

Run only with the fixed protocol in docs/rain-leading-signal-protocol.json.
Historical rain receipt times are unknown, so this cannot promote a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from hydro_propagation_model import (
    ALPHAS, EMBARGO_HOURS, REQUIRED, TARGET, epoch, feature_matrix, fit_ridge,
    infer_delta, metrics, shift, split_rows, validate_series,
)

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('Baixo Antas', 'Carreiro', 'Prata-Turvo', 'Alto Antas', 'Tainhas')
WINDOWS = (3, 6, 12, 24)


def rain_matrix(hourly_times, archived):
    quarter_times = archived['times']
    # The audited archive is an exact quarter-hour grid. The reading ending at
    # t-1h is the latest admissible rain input at prediction origin t.
    if np.any(np.diff(quarter_times) != 900):
        raise ValueError('Rain archive must have an exact quarter-hour grid')
    index = np.searchsorted(quarter_times, hourly_times - 3600)
    aligned = (index < len(quarter_times)) & (quarter_times[np.minimum(index, len(quarter_times)-1)] == hourly_times - 3600)
    safe = np.minimum(index, len(quarter_times)-1)
    columns, names = [], []
    complete = aligned.copy()
    for group in GROUPS:
        for window in WINDOWS:
            rain = archived[f'{group}:rain{window}'][safe]
            coverage = archived[f'{group}:cover{window}'][safe]
            valid = aligned & np.isfinite(rain) & (rain >= 0) & np.isfinite(coverage) & (coverage >= .5)
            complete &= valid
            columns.append(np.where(valid, rain / 100, np.nan))
            names.append(f'{group}:observed_P{window}_ending_t_minus_1h/100mm')
    return np.column_stack(columns), names, complete


def subset(pred, actual, base, mask):
    if not mask.any():
        return {'n': 0}
    return metrics(pred[mask], actual[mask], base[mask])


def finite_ridge_prediction(features, delta, train, evaluate, alpha):
    # Some Accelerate/NumPy builds report floating-point flags raised inside
    # BLAS even when the finite ridge solution is well defined. Verify every
    # coefficient and prediction explicitly rather than trusting the warning.
    with np.errstate(divide='ignore', over='ignore', invalid='ignore'):
        fitted = fit_ridge(features, delta, train, alpha)
        predicted = infer_delta(fitted, features[evaluate])
    if not all(np.isfinite(fitted[key]).all() for key in ('mean', 'scale', 'beta')) or not np.isfinite(predicted).all():
        raise ArithmeticError('Nonfinite ridge fit or prediction')
    return predicted


def evaluate_pair(base_pred, rain_pred, actual, initial, regional_rain6, quiet):
    masks = {
        'all': np.ones(len(actual), dtype=bool),
        'high_water_7m': actual >= 7,
        'rapid_rise_1m': actual - initial >= 1,
        'rain6_at_least_20mm': regional_rain6 >= 20,
        'rain6_at_least_50mm': regional_rain6 >= 50,
        'rain6_at_least_100mm': regional_rain6 >= 100,
        'quiet_hydrometry_rain6_at_least_20mm': quiet & (regional_rain6 >= 20),
        'quiet_hydrometry_rain6_at_least_50mm': quiet & (regional_rain6 >= 50),
    }
    result = {}
    for name, mask in masks.items():
        first = subset(base_pred, actual, initial, mask)
        second = subset(rain_pred, actual, initial, mask)
        result[name] = {
            'n': first['n'],
            'hydrometric_mae_m': first.get('mae_m'),
            'rain_mae_m': second.get('mae_m'),
            'hydrometric_within_50cm_rate': first.get('within_50cm_rate'),
            'rain_within_50cm_rate': second.get('within_50cm_rate'),
            'rain_false_rise_n': int(np.sum(mask & (rain_pred-initial >= 1) & (actual-initial < .5))),
            'hydrometric_false_rise_n': int(np.sum(mask & (base_pred-initial >= 1) & (actual-initial < .5))),
        }
    return result


def run(hydro_path, rain_path, model_path, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    if protocol['id'] != 'rain-leading-signal-v1' or protocol['promotionEligible'] is not False:
        raise ValueError('Unexpected experiment protocol')
    model = json.loads(model_path.read_text())
    hydro, archived = np.load(hydro_path), np.load(rain_path)
    times, data = validate_series(hydro['times'], hydro)
    rainfall, rain_names, rain_valid = rain_matrix(times, archived)
    local = data[TARGET]
    # Fixed lag parameters and hydrometric feature family are inherited from
    # the already frozen public artifact; this experiment never retunes them.
    if len(model['horizons']) != 6 or any(row['parameters']['alpha'] not in ALPHAS for row in model['horizons']):
        raise ValueError('Unexpected public model artifact')
    rain6 = np.max(np.where(np.isfinite(rainfall[:, 1::4]), rainfall[:, 1::4] * 100, -np.inf), axis=1)
    rain6[~np.isfinite(rain6)] = np.nan
    local_slope = abs((local-shift(local, 3))/3)
    # Discharge is considered quiet only if each observed downstream discharge
    # differs by <=10% over three hours. This is diagnostic, not hydraulic QC.
    quiet = np.isfinite(local_slope) & (local_slope <= .05)
    for key in ('julho:Q', 'monte:Q', 'castro:Q'):
        now, past = data[key], shift(data[key], 3)
        quiet &= np.isfinite(now) & np.isfinite(past) & (abs(now-past) <= .1 * np.maximum(past, 100))
    reports = []
    predictions = []
    for row in model['horizons']:
        h = row['h']
        base_features, base_names = feature_matrix(data, model['lags'], row['family'])
        if base_names != row['featureNames']:
            raise ValueError(f'Public hydrometric feature contract changed at H+{h}')
        rain_features = np.column_stack((base_features, rainfall))
        target = shift(local, -h)
        valid = rain_valid & np.isfinite(base_features).all(axis=1) & np.isfinite(target)
        rows = split_rows(times, valid, h, model['trainingCutoff'], model['validationCutoff'], model['testCutoff'], EMBARGO_HOURS)
        if len(rows['train']) < 96 or len(rows['validation']) < 48:
            raise ValueError(f'Insufficient common train/validation support for H+{h}')
        delta = target - local
        phase_fit = {
            'validation': rows['train'],
            'test': np.r_[rows['train'], rows['validation']],
            'stress_current': np.r_[rows['train'], rows['validation']],
        }
        for phase in ('validation', 'test', 'stress_current'):
            indices = rows[phase]
            if not len(indices):
                continue
            fit = phase_fit[phase]
            alpha = row['parameters']['alpha']
            base_pred = local[indices] + finite_ridge_prediction(base_features, delta, fit, indices, alpha)
            rain_pred = local[indices] + finite_ridge_prediction(rain_features, delta, fit, indices, alpha)
            actual = target[indices]
            reports.append({'h': h, 'phase': phase, 'trainingRows': len(fit), 'evaluationRows': len(indices),
                            'strata': evaluate_pair(base_pred, rain_pred, actual, local[indices], rain6[indices], quiet[indices])})
            predictions.extend({'h': h, 'phase': phase, 'origin': float(times[i]), 'actual_m': float(y),
                                'base_m': float(local[i]), 'hydrometric_m': float(b), 'rain_m': float(r),
                                'max_regional_rain6_mm': float(rain6[i]), 'quiet_hydrometry': bool(quiet[i])}
                               for i, y, b, r in zip(indices, actual, base_pred, rain_pred))
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (hydro_path, rain_path, model_path, protocol_path, Path(__file__))}
    return {'schema': protocol['id'], 'sourceSha256': hashes, 'rainFeatureNames': rain_names,
            'limitations': ['Historical rainfall arrival time is not reconstructed; t-1h is an assumed availability margin.',
                            'The test dates and September flood were previously inspected during model development.',
                            'The sample does not include the major 2024 floods or prove live forecast accuracy.'],
            'reports': reports}, predictions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hydro', type=Path, default=ROOT/'outputs/propagacao-dados-20260923/exact-hour-level-flow.npz')
    ap.add_argument('--rain', type=Path, default=ROOT/'outputs/mucum-auditoria-2026-09-21/telemetria-corrigida.npz')
    ap.add_argument('--model', type=Path, default=ROOT/'model-artifacts/mucum-propagation-v1/model.json')
    ap.add_argument('--protocol', type=Path, default=ROOT/'docs/rain-leading-signal-protocol.json')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report, predictions = run(args.hydro, args.rain, args.model, args.protocol)
    (args.output/'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    (args.output/'predictions.json').write_text(json.dumps(predictions, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps([{'h': r['h'], 'phase': r['phase'], 'all': r['strata']['all'],
                       'quiet_rain': r['strata']['quiet_hydrometry_rain6_at_least_20mm']}
                      for r in report['reports']], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
