"""Isolate the effect of reservoir-level flow predictors on Muçum hindcasts.

No fitting, live issuance or promotion. All historical availability assumptions
and exclusions are explicit. Future upstream observations never select origins.
"""
import argparse, csv, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits
from hydro_hourly_forecast import ROOT, BASE, epoch, iso, dump
from hydro_hourly_models import upstream_features
from hydro_upstream_audit import predict_many, savecsv
from hydro_hge_dependencies import weather

FLOW = ROOT/'outputs/experimento-niveis-reservatorios-20260921'
HGE = ROOT/'experiments/hge-water-balance'


def route(history, forecast, weights, lags, origin_index, horizon):
    """Nonnegative relative lead must use inference, never historical truth."""
    if len(weights) != len(lags):
        raise ValueError('Kernel length mismatch')
    total = 0.
    for weight, lag in zip(weights, lags):
        k = horizon-lag
        if k >= 0:
            value = forecast[k]
        else:
            j = origin_index+k
            if j < 0:
                raise ValueError('Insufficient historical prefix')
            value = history[j]
        if not np.isfinite(value):
            return np.nan
        total += weight*value
    return total


def anchor_index(grid, origin, delay_seconds=900):
    at = origin-delay_seconds; index = int(np.searchsorted(grid, at))
    if index == len(grid) or grid[index] != at:
        return None
    return index


def score(rows, high):
    eligible = [r for r in rows if r['actual_m'] is not None and (not high or r['actual_m'] >= 7)]
    paired = [r for r in eligible if r['status'] == 'paired']
    results = []
    for family in ['reference', 'julho_levels']:
        e = np.array([r[family+'_m']-r['actual_m'] for r in paired]); ae = abs(e)
        results.append({'family': family, 'subset': 'level_ge_7m' if high else 'all',
                        'observed_targets': len(eligible), 'paired_n': len(e),
                        'forecast_failures_with_truth': len(eligible)-len(e),
                        'coverage': len(e)/len(eligible) if eligible else None,
                        'within_0_50_n': int((ae <= .5).sum()),
                        'within_0_50_fraction': float((ae <= .5).mean()) if len(e) else None,
                        'mae_m': float(ae.mean()) if len(e) else None,
                        'bias_m': float(e.mean()) if len(e) else None,
                        'p90_abs_m': float(np.quantile(ae, .9)) if len(e) else None,
                        'p98_abs_m': float(np.quantile(ae, .98)) if len(e) else None,
                        'max_abs_m': float(ae.max()) if len(e) else None})
    return results


def run(out, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    if protocol['horizons_h'] != list(range(1, 13)) or protocol['families'] != ['reference', 'julho_levels']:
        raise ValueError('Unsupported protocol')
    out.mkdir(parents=True, exist_ok=False); (out/'protocol.json').write_bytes(protocol_path.read_bytes())
    paths = [protocol_path, FLOW/'frozen-models.json', FLOW/'additional-features.npz', FLOW/'predictions.csv',
             FLOW/'experiment.json', BASE/'dados-roteamento.npz', BASE/'telemetria-latencia.npz',
             BASE/'roteamento-vazao-pesos.csv', BASE/'conferencia-balanco.json',
             ROOT/'outputs/mucum-hge-experimental-2026-09-21/parametros.json',
             ROOT/'outputs/mucum-hge-experimental-2026-09-21/resultado.json', HGE/'run.py', HGE/'vendor/hydrological_model.py',
             Path(__file__), ROOT/'scripts/hydro_hourly_models.py', ROOT/'scripts/hydro_upstream_audit.py',
             ROOT/'scripts/hydro_hge_dependencies.py', ROOT/'scripts/hydro_hourly_forecast.py']
    oldmanifest = json.loads((FLOW/'artifact-hashes.json').read_text())
    for p in paths:
        if p.parent == FLOW:
            expected = next(r['sha256'] for r in oldmanifest if r['file'] == p.name)
            if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError('Changed flow experiment '+str(p))
    hgemeta = json.loads((ROOT/'outputs/mucum-hge-experimental-2026-09-21/resultado.json').read_text())
    if epoch(hgemeta['calibration']['end_exclusive']) != epoch('2026-07-01T00:00:00-03:00'):
        raise ValueError('Unexpected HGE calibration boundary')
    d = dict(np.load(BASE/'dados-roteamento.npz')); z = dict(np.load(BASE/'telemetria-latencia.npz'))
    t = d['times']; leveldata = dict(np.load(FLOW/'additional-features.npz'))
    np.testing.assert_array_equal(leveldata['times'], t)
    F = upstream_features(z, t); extended = np.column_stack([F, leveldata['levels_and_slopes']])
    models = json.loads((FLOW/'frozen-models.json').read_text()); f = {}
    for source, key in [('julho', 'julho:Q'), ('carreiro', '86500000:Q')]:
        known = z[key][np.searchsorted(z['times'], t)]/1000
        for family in (['reference', 'level_and_slopes'] if source == 'julho' else ['reference']):
            X = F if family == 'reference' else extended
            f[source, family] = np.column_stack([np.maximum(known+predict_many(
                {k: np.array(v) if isinstance(v, list) else v for k, v in models[f'{source}:{lead}:test:{family}'].items()}, X), 0)*1000
                for lead in range(12)])
    # Independently confirm the already-preserved upstream evaluation values.
    lookup = {iso(at): i for i, at in enumerate(t)}; max_flow_error = 0.
    for r in csv.DictReader((FLOW/'predictions.csv').open()):
        if r['phase'] != 'test' or (r['source'], r['family']) not in f:
            continue
        got = f[r['source'], r['family']][lookup[r['origin']], int(r['lead_h'])]
        max_flow_error = max(max_flow_error, abs(got-float(r['forecast_m3_s'])))
    if max_flow_error > 1e-7:
        raise ValueError('Frozen flow predictions not reproduced')
    spec = importlib.util.spec_from_file_location('hge_reservoir_mucum', HGE/'run.py')
    hge = importlib.util.module_from_spec(spec); spec.loader.exec_module(hge)
    pars = next(r['parameters'] for r in json.loads(paths[9].read_text()) if r['pet_mm_day_hypothesis'] == 3)
    pars = np.array([pars[k] for k in hge.NAMES]); balance = json.loads((BASE/'conferencia-balanco.json').read_text())
    rating = balance['rating_parameters']; area = float(d['area'])
    kernel_rows = list(csv.DictReader((BASE/'roteamento-vazao-pesos.csv').open()))
    weights = {s: np.array([float(r['weight']) for r in kernel_rows if r['source'] == name])
               for s, name in [('julho', '14 de Julho'), ('carreiro', 'Passo Carreiro')]}
    if any(abs(w.sum()-1) > 1e-6 or w.min() < 0 for w in weights.values()):
        raise ValueError('Nonconservative routing kernel')
    members = []
    for model in ['gfs_seamless', 'ecmwf_ifs025', 'icon_global']:
        path = BASE/'nwp-historical-icon.json' if model == 'icon_global' else ROOT/'outputs/mucum-propagacao-2026-09-21/raw'/f'chuva-previsao-historica-{model}.json'
        paths.append(path); values, _ = weather(path, t, 'precipitation_previous_day1'); members.append(values)
    count = np.isfinite(members).sum(axis=0)
    if np.any(count == 0): raise ValueError('Missing all rainfall forecasts')
    mean = np.nansum(members, axis=0)/count
    rain = d['amount']+np.maximum(1-d['coverage'], 0)*mean
    states, errors = hge.simulate(rain, 3., pars, area, hge.initial_state(pars))
    if np.max(abs(errors)) > 1e-8: raise ValueError('Historical numerical water balance failed')
    input_hashes = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    cutoff = epoch('2026-09-21T00:00:00-03:00')
    origins = np.where((t >= epoch('2026-07-01T00:00:00-03:00')) & (t < cutoff))[0]
    result = []; numerical_error = float(np.max(abs(errors)))
    upstream_history = {s: d[s]*1000 for s in ['julho', 'carreiro']}
    for sequence, i in enumerate(origins):
        ai = anchor_index(z['times'], t[i]); anchor_h = z['raw:86510000:H'][ai] if ai is not None else np.nan
        anchor_q = z['raw:86510000:Q'][ai] if ai is not None else np.nan
        local, err = hge.simulate(mean[i:i+13], 3., pars, area, states[i-1].copy())
        numerical_error = max(numerical_error, float(np.max(abs(err))))
        def routed(h, family):
            return sum(route(upstream_history[s], f[s, family if s == 'julho' else 'reference'][i], weights[s],
                             range(1, 13) if s == 'julho' else range(4, 25), i, h) for s in ['julho', 'carreiro'])
        previous_q = routed(-1, 'reference')+states[i-1, -1]
        origin_q = routed(0, 'reference')+local[0, -1]
        # Common interpolation to origin-15min; both endpoints use past upstream inputs.
        reconstructed_anchor = .25*previous_q+.75*origin_q
        residual = anchor_q-reconstructed_anchor
        offset = anchor_h-float(hge.stage(anchor_q, rating)) if np.isfinite(anchor_q) else np.nan
        for horizon in range(1, 13):
            if t[i]+horizon*3600 >= cutoff: continue
            actual = float(d['h'][i+horizon]); predictions = {}
            for label, family in [('reference', 'reference'), ('julho_levels', 'level_and_slopes')]:
                q = routed(horizon, family)+local[horizon, -1]+residual*np.exp(-(horizon+.25)/6)
                predictions[label+'_m'] = float(hge.stage(q, rating)+offset) if np.isfinite(q) and q >= 0 else None
            if not np.isfinite(anchor_h) or not np.isfinite(anchor_q): status = 'missing_exact_anchor'
            elif any(v is None or not np.isfinite(v) for v in predictions.values()): status = 'missing_or_invalid_forecast_input'
            elif not np.isfinite(actual): status = 'missing_exact_target'
            else: status = 'paired'
            row = {'origin': iso(t[i]), 'target_time': iso(t[i]+horizon*3600), 'nominal_lead_h': horizon,
                   'anchor_at': iso(t[i]-900), 'state_rain_observations_end_at': iso(t[i]-3600),
                   'actual_m': actual if np.isfinite(actual) else None,
                   **predictions, 'status': status,
                   'upstream_target_observation_missing': bool(not np.isfinite(d['julho'][i+horizon-1]))}
            result.append(row)
        if sequence % 300 == 0: print('origins', sequence, '/', len(origins), flush=True)
    evaluations = []
    for horizon in range(1, 13):
        subset = [r for r in result if r['nominal_lead_h'] == horizon]
        for high in [False, True]:
            evaluations.extend([{'nominal_lead_h': horizon, **r} for r in score(subset, high)])
    savecsv(out/'predictions.csv', result); savecsv(out/'evaluation.csv', evaluations)
    if numerical_error > 1e-8: raise ValueError('Future water balance failed')
    for path, digest in input_hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest: raise ValueError('Changed during run '+path)
    (out/'code').mkdir()
    for path in paths:
        if path.suffix == '.py': (out/'code'/path.name).write_bytes(path.read_bytes())
    dump(out/'experiment.json', {'input_sha256': input_hashes, 'status_counts': dict(Counter(r['status'] for r in result)),
                                'origin_count': len(origins), 'scheduled_target_pairs': len(result),
                                'upstream_reproduction_max_error_m3_s': max_flow_error,
                                'max_numerical_balance_error_mm': numerical_error,
                                'fitted_here': False, 'status': 'Previously inspected historical development only',
                                'paired_with_missing_upstream_target': sum(r['status'] == 'paired' and r['upstream_target_observation_missing'] for r in result),
                                'historical_availability_verified': False, 'promoted': False, 'live_issuance': False, 'goal_achieved': False})
    print(json.dumps({'output': str(out), 'statuses': dict(Counter(r['status'] for r in result))}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=ROOT/'docs/reservoir-level-mucum-protocol.json')
    args = parser.parse_args()
    with threadpool_limits(limits=2): run(args.output, args.protocol)
