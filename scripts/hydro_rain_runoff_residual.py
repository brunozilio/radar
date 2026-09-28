"""Frozen paired experiment: age-specific observed rain as bounded runoff signal.

This is an exploratory candidate. Retrospective rainfall arrival times are not
proven, and its artifact must not be used for the public numeric forecast.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from hydro_propagation_model import (
    EMBARGO_HOURS, TARGET, feature_matrix, fit_ridge, infer_delta, metrics,
    shift, split_rows, validate_series,
)

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('Baixo Antas', 'Carreiro', 'Prata-Turvo', 'Alto Antas', 'Tainhas')
WINDOWS = (3, 6, 12, 24)
PULSE_CAP_MM = 40.0
UPLIFT_CAP_M = .35
ALPHA = 10.0


def rain_age_matrix(hourly_times, archived):
    """Rainfall in disjoint age bins, with an exact one-hour publication margin."""
    quarter = np.asarray(archived['times'], dtype=float)
    if not len(quarter) or np.any(np.diff(quarter) != 900):
        raise ValueError('Rain archive must be a continuous quarter-hour grid')
    lookup = np.searchsorted(quarter, hourly_times - 3600)
    safe = np.minimum(lookup, len(quarter)-1)
    aligned = (lookup < len(quarter)) & (quarter[safe] == hourly_times - 3600)
    names, columns, raw_columns = [], [], []
    complete = aligned.copy()
    for group in GROUPS:
        cumulative = []
        for window in WINDOWS:
            amount = np.asarray(archived[f'{group}:rain{window}'][safe], dtype=float)
            coverage = np.asarray(archived[f'{group}:cover{window}'][safe], dtype=float)
            valid = aligned & np.isfinite(amount) & (amount >= 0) & np.isfinite(coverage) & (coverage >= .5)
            complete &= valid
            cumulative.append(amount)
        # Small negative differences can arise from independently corrected
        # area-weighted windows. Never convert them into negative precipitation.
        pulse = [cumulative[0]] + [np.maximum(0, cumulative[i]-cumulative[i-1]) for i in range(1, 4)]
        for label, amount in zip(('0_3', '3_6', '6_12', '12_24'), pulse):
            raw_columns.append(amount)
            columns.append(np.clip(amount, 0, PULSE_CAP_MM) / 100.0)
            names.append(f'{group}:observed_rain_age_{label}h_ending_t_minus_1h')
    return np.column_stack(columns), np.column_stack(raw_columns), names, complete


def fit_nonnegative_ridge(features, residual, rows, alpha=ALPHA):
    """Solve a small strictly convex nonnegative ridge by cyclic coordinates."""
    x = np.asarray(features[rows], dtype=float)
    y = np.asarray(residual[rows], dtype=float)
    if not len(rows) or not np.isfinite(x).all() or not np.isfinite(y).all() or alpha <= 0:
        raise ValueError('Rain fit requires finite training rows and positive regularization')
    # Apple's Accelerate sometimes sets floating-point status flags inside
    # finite BLAS operations; check the resulting arrays explicitly.
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        gram = x.T @ x
        cross = x.T @ y
    if not np.isfinite(gram).all() or not np.isfinite(cross).all():
        raise ArithmeticError('Nonfinite rainfall ridge inputs')
    beta = np.zeros(x.shape[1], dtype=float)
    for _ in range(2000):
        before = beta.copy()
        for j in range(len(beta)):
            partial = cross[j] - gram[j] @ beta + gram[j, j] * beta[j]
            beta[j] = max(0.0, partial / (gram[j, j] + alpha))
        if np.max(np.abs(beta-before)) < 1e-11:
            break
    if not np.isfinite(beta).all():
        raise ArithmeticError('Nonfinite rain response')
    return beta


def bounded_uplift(features, beta):
    values = np.asarray(features, dtype=float)
    coefficients = np.asarray(beta, dtype=float)
    if values.shape[-1] != len(coefficients) or not np.isfinite(values).all() or not np.isfinite(coefficients).all() or np.any(coefficients < 0):
        raise ValueError('Invalid rainfall inputs or coefficients')
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        result = values @ coefficients
    if not np.isfinite(result).all():
        raise ArithmeticError('Nonfinite rainfall uplift')
    return np.clip(result, 0, UPLIFT_CAP_M)


def episode_count(times, flagged, separation_hours=24):
    selected = times[flagged]
    return int(len(selected) and 1 + np.sum(np.diff(selected) > separation_hours * 3600))


def assess(base_pred, candidate, actual, origin, raw_pulses, quiet, times):
    # Sum the two youngest disjoint pulses for a real six-hour accumulation.
    max_rain6 = np.max(raw_pulses[:, 0::4] + raw_pulses[:, 1::4], axis=1)
    masks = {
        'all': np.ones(len(actual), dtype=bool),
        'high_water_7m': actual >= 7,
        'rapid_rise_1m': actual - origin >= 1,
        'rain6_at_least_20mm': max_rain6 >= 20,
        'rain6_at_least_50mm': max_rain6 >= 50,
        'rain6_at_least_100mm': max_rain6 >= 100,
        'quiet_hydrometry_rain6_at_least_20mm': quiet & (max_rain6 >= 20),
        'quiet_hydrometry_rain6_at_least_50mm': quiet & (max_rain6 >= 50),
        'rain_input_exceeds_40mm_age_bin': np.any(raw_pulses > PULSE_CAP_MM, axis=1),
    }
    result = {}
    for name, mask in masks.items():
        a = metrics(base_pred[mask], actual[mask], origin[mask]) if mask.any() else {'n': 0}
        b = metrics(candidate[mask], actual[mask], origin[mask]) if mask.any() else {'n': 0}
        result[name] = {
            'n': a['n'], 'episodes_separated_24h': episode_count(times, mask),
            'hydrometric_mae_m': a.get('mae_m'), 'rain_mae_m': b.get('mae_m'),
            'hydrometric_within_50cm_rate': a.get('within_50cm_rate'),
            'rain_within_50cm_rate': b.get('within_50cm_rate'),
            'hydrometric_false_rise_n': int(np.sum(mask & (base_pred-origin >= 1) & (actual-origin < .5))),
            'rain_false_rise_n': int(np.sum(mask & (candidate-origin >= 1) & (actual-origin < .5))),
        }
    return result


def run(hydro_path, rain_path, model_path, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    if protocol['id'] != 'rain-runoff-residual-v1' or protocol['promotionEligible'] is not False:
        raise ValueError('Unexpected research protocol')
    model = json.loads(model_path.read_text())
    hydro, archived = np.load(hydro_path), np.load(rain_path)
    times, data = validate_series(hydro['times'], hydro)
    rain, raw_pulses, names, rain_valid = rain_age_matrix(times, archived)
    local = data[TARGET]
    rain6 = np.max((raw_pulses[:, 0::4] + raw_pulses[:, 1::4]), axis=1)
    quiet = np.isfinite(local) & np.isfinite(shift(local, 3)) & (abs(local-shift(local, 3))/3 <= .05)
    for key in ('julho:Q', 'monte:Q', 'castro:Q'):
        current, earlier = data[key], shift(data[key], 3)
        quiet &= np.isfinite(current) & np.isfinite(earlier) & (abs(current-earlier) <= .1*np.maximum(earlier, 100))
    reports, predictions, artifact_horizons = [], [], []
    for horizon in model['horizons']:
        h = int(horizon['h'])
        base_features, base_names = feature_matrix(data, model['lags'], horizon['family'])
        if base_names != horizon['featureNames']:
            raise ValueError(f'Public hydrometric feature contract changed at H+{h}')
        target = shift(local, -h)
        valid = rain_valid & np.isfinite(base_features).all(axis=1) & np.isfinite(target)
        splits = split_rows(times, valid, h, model['trainingCutoff'], model['validationCutoff'], model['testCutoff'], EMBARGO_HOURS)
        if len(splits['train']) < 96 or len(splits['validation']) < 48:
            raise ValueError(f'Insufficient common support for H+{h}')
        delta = target-local
        final_parameters = final_beta = None
        for phase in ('validation', 'test', 'stress_current'):
            evaluate = splits[phase]
            fit = splits['train'] if phase == 'validation' else np.r_[splits['train'], splits['validation']]
            with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                parameters = fit_ridge(base_features, delta, fit, horizon['parameters']['alpha'])
                training_base = infer_delta(parameters, base_features[fit])
                base_pred = local[evaluate] + infer_delta(parameters, base_features[evaluate]) if len(evaluate) else np.empty(0)
            # fit_nonnegative_ridge expects a full-length residual vector.
            residual = np.full(len(times), np.nan)
            residual[fit] = delta[fit]-training_base
            beta = fit_nonnegative_ridge(rain, residual, fit, ALPHA)
            if phase == 'test':
                final_parameters, final_beta = parameters, beta
            if not len(evaluate):
                continue
            candidate = base_pred + bounded_uplift(rain[evaluate], beta)
            reports.append({
                'h': h, 'phase': phase, 'trainingRows': int(len(fit)), 'evaluationRows': int(len(evaluate)),
                'strata': assess(base_pred, candidate, target[evaluate], local[evaluate],
                                 raw_pulses[evaluate], quiet[evaluate], times[evaluate]),
            })
            predictions.extend({
                'h': h, 'phase': phase, 'origin': float(times[i]), 'actual_m': float(target[i]),
                'origin_m': float(local[i]), 'hydrometric_m': float(b), 'rain_candidate_m': float(c),
                'max_regional_rain6_mm': float(rain6[i]), 'rain_input_cap_exceeded': bool(np.any(raw_pulses[i] > PULSE_CAP_MM)),
                'quiet_hydrometry': bool(quiet[i]),
            } for i, b, c in zip(evaluate, base_pred, candidate))
        artifact_horizons.append({
            'h': h, 'hydrometricFamily': horizon['family'], 'hydrometricAlpha': horizon['parameters']['alpha'],
            'hydrometricParameters': final_parameters, 'rainResponseCoefficients': final_beta.tolist(),
            'trainValidationRows': int(len(splits['train'])+len(splits['validation'])),
        })
    def source_name(path):
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError:
            return f'external:{path.name}'
    hashes = {source_name(path): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (hydro_path, rain_path, model_path, protocol_path, Path(__file__))}
    artifact = {
        'contract': protocol['id'], 'promotionEligible': False, 'targetStation': '86510000',
        'observedRainMarginHours': 1, 'rainFeatureNames': names, 'rainPulseCapMm': PULSE_CAP_MM,
        'upliftCapM': UPLIFT_CAP_M, 'ridgeAlpha': ALPHA, 'hydrometricLags': model['lags'],
        'historicalRainReceiptVerified': False, 'sourceSha256': hashes, 'horizons': artifact_horizons,
    }
    report = {'contract': protocol['id'], 'promotionEligible': False, 'sourceSha256': hashes,
              'rainFeatureNames': names, 'limitations': [
                  'Rain receipt time at historical origins is unverified.',
                  'No issued precipitation forecasts are included; upcoming rain cannot be seen.',
                  'The test and September stress events were previously inspected in model development.',
                  'Continuous rainy hours are dependent; episode counts do not establish independent flood validation.',
              ], 'reports': reports}
    return report, artifact, predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hydro', type=Path, default=ROOT/'outputs/propagacao-dados-20260923/exact-hour-level-flow.npz')
    parser.add_argument('--rain', type=Path, default=ROOT/'outputs/mucum-auditoria-2026-09-21/telemetria-corrigida.npz')
    parser.add_argument('--model', type=Path, default=ROOT/'model-artifacts/mucum-propagation-v1/model.json')
    parser.add_argument('--protocol', type=Path, default=ROOT/'docs/rain-runoff-residual-protocol-2026-09-28.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report, artifact, predictions = run(args.hydro, args.rain, args.model, args.protocol)
    for name, value in (('report.json', report), ('model.json', artifact), ('predictions.json', predictions)):
        (args.output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps([{'h': r['h'], 'phase': r['phase'], 'all': r['strata']['all'],
                       'rain50': r['strata']['rain6_at_least_50mm']} for r in report['reports']],
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
