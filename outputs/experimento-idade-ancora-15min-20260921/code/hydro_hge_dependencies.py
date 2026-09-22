"""Replay a preserved HGE issue and attribute routed flow, without issuing forecasts.

Persistence is a counterfactual sensitivity only, not a candidate promotion or
physical bound. Read exclusively hash-verified receipt/artifact blobs.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from hydro_prospective_ledger import DEFAULT, read_records

TZ = timezone(timedelta(hours=-3))
MODELS = ['gfs_seamless', 'ecmwf_ifs025', 'icon_global']


def epoch(value):
    dt = datetime.fromisoformat(value)
    return (dt if dt.tzinfo else dt.replace(tzinfo=TZ)).timestamp()


def routing_parts(history, future, weights, lags, lead, known):
    """Partition a routing kernel by whether its inputs are historical or modeled."""
    observed = modeled = persisted = future_weight = 0.
    if len(weights) != len(lags) or abs(sum(weights)-1) > 1e-6 or min(weights) < 0:
        raise ValueError('Invalid routing kernel')
    for lag, weight in zip(lags, weights):
        k = lead-lag
        if k < 0:
            value = history[len(history)-1+k]
            observed += weight*value
        else:
            value = future[k]
            modeled += weight*value
            persisted += weight*known
            future_weight += weight
        if not np.isfinite(value):
            raise ValueError('Missing routing input')
    return observed, modeled, persisted, future_weight


def weather(path, times, field):
    data = json.loads(path.read_text())[0]
    if data['utc_offset_seconds'] != -10800 or data['hourly_units'][field] != 'mm':
        raise ValueError('Weather contract mismatch')
    h = data['hourly']; lookup = {epoch(t): v for t, v in zip(h['time'], h[field])}
    return np.array([lookup.get(t, np.nan) for t in times], dtype=float), h['time']


def run(packet_path, out, ledger):
    packet = json.loads(packet_path.read_text())
    records = read_records(ledger); by_sha = {r['sha256']: r for r in records}
    issue = next(r for r in records if r['kind'] == 'forecast_issue' and r['payload'] == packet)
    verified = []; inputs = {}; artifacts = {}
    def preserve(path, blob, digest, container):
        source = ledger/blob
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError('Changed blob: '+blob)
        container[path] = source
        verified.append({'source_path': path, 'blob': blob, 'sha256': digest})
    for receipt in packet['input_receipts']:
        item = by_sha[receipt]['payload']
        preserve(item['source_path'], item['blob'], item['blob_sha256'], inputs)
    for item in packet['model_artifacts']:
        preserve(item['path'], item['blob'], item['sha256'], artifacts)
    def find(mapping, suffix):
        matches = [v for k, v in mapping.items() if k.endswith(suffix)]
        if len(matches) != 1:
            raise ValueError('Ambiguous/missing input: '+suffix)
        return matches[0]
    out.mkdir(parents=True, exist_ok=False)
    code = out/'code'; (code/'vendor').mkdir(parents=True)
    (code/'run.py').write_bytes(find(artifacts, '/hge-water-balance/run.py').read_bytes())
    (code/'vendor/hydrological_model.py').write_bytes(find(artifacts, '/vendor/hydrological_model.py').read_bytes())
    spec = importlib.util.spec_from_file_location('hge_dependency_replay', code/'run.py')
    hge = importlib.util.module_from_spec(spec); spec.loader.exec_module(hge)
    d = dict(np.load(find(inputs, '/dados-roteamento.npz')))
    z = dict(np.load(find(inputs, '/telemetria-latencia.npz')))
    saved = dict(np.load(find(artifacts, '/models/hge-state.npz')))
    times = d['times']; origin = epoch(packet['reference_at'])
    assert times[-1] == origin
    leads = [p['nominal_lead_h'] for p in packet['points']]
    alltimes = np.r_[times, origin+np.arange(1, max(leads)+1)*3600]
    members = []
    for model in MODELS:
        suffix = '/nwp-historical-icon.json' if model == 'icon_global' else f'/chuva-previsao-historica-{model}.json'
        old, _ = weather(find(inputs, suffix), alltimes, 'precipitation_previous_day1')
        live, covered_times = weather(find(inputs, f'/history/weather-{model}.json'), alltimes, 'precipitation')
        covered = (alltimes >= epoch(covered_times[0])) & (alltimes <= epoch(covered_times[-1]))
        old[covered] = live[covered]; members.append(old)
    members = np.array(members); count = np.isfinite(members).sum(axis=0)
    if np.any(count == 0):
        raise ValueError('All weather members missing')
    mean = np.nansum(members, axis=0)/count
    rain = d['amount']+np.maximum(0, 1-d['coverage'])*mean[:len(times)]
    states, errors = hge.simulate(rain, 3., saved['parameters'], float(d['area']), hge.initial_state(saved['parameters']))
    np.testing.assert_allclose(states[-1], saved['state'], rtol=0, atol=1e-8)
    future, future_errors = hge.simulate(mean[len(times):], 3., saved['parameters'], float(d['area']), saved['state'].copy())
    zero_rain, zero_errors = hge.simulate(np.zeros(len(future)), 3., saved['parameters'], float(d['area']), saved['state'].copy())
    max_balance = float(max(np.max(abs(e)) for e in [errors, future_errors, zero_errors]))
    if max_balance > 1e-8:
        raise ValueError('Water balance mismatch')
    past = (d['X'][:, :12]@saved['julho']+d['X'][:, 12:33]@saved['carreiro'])*1000+states[:, -1]
    at = epoch(packet['last_observed']['last_time']); oi = np.searchsorted(z['times'], at)
    assert z['times'][oi] == at
    baseq = float(z['raw:86510000:Q'][oi]); baseh = float(z['raw:86510000:H'][oi])
    assert baseh == packet['last_observed']['value']
    residual = baseq-float(np.interp(at, times[-25:], past[-25:])); age = (origin-at)/3600
    offset = baseh-float(hge.stage(baseq, saved['rating']))
    diagnostics = json.loads(find(artifacts, '/upstream-extrapolation.json').read_text())
    flow = {s: {r['lead_h']: r['forecast_m3_s'] for r in diagnostics if r['source'] == s} for s in ['julho', 'carreiro']}
    rows = []
    for point in packet['points']:
        lead = point['nominal_lead_h']; row = {'lead_h': lead, 'valid_at': point['valid_at']}
        total = persisted = 0.
        for source, key, lags in [('julho', 'julho:Q', range(1, 13)), ('carreiro', '86500000:Q', range(4, 25))]:
            observed, modeled, constant, weight = routing_parts(d[source]*1000, flow[source], saved[source], lags, lead, z[key][-1])
            row.update({f'{source}_history_m3_s': observed, f'{source}_modeled_m3_s': modeled,
                        f'{source}_persistence_m3_s': constant, f'{source}_modeled_kernel_weight': weight})
            total += observed+modeled; persisted += observed+constant
        local = float(future[lead-1, -1]); correction = float(residual*np.exp(-(lead+age)/6))
        q = total+local+correction
        prediction = float(hge.stage(q, saved['rating'])+offset)
        persistence_q = persisted+local+correction
        no_new_rain_q = total+zero_rain[lead-1, -1]+correction
        if min(q, persistence_q, no_new_rain_q) < 0 or not np.isfinite([q, persistence_q, no_new_rain_q]).all():
            raise ValueError('Invalid sensitivity flow')
        row.update({'local_runoff_m3_s': local, 'anchor_correction_m3_s': correction, 'total_m3_s': q,
                    'level_m': prediction, 'replay_error_m': prediction-point['level_m'],
                    'upstream_persistence_level_m': float(hge.stage(persistence_q, saved['rating'])+offset),
                    'no_new_local_rain_level_m': float(hge.stage(no_new_rain_q, saved['rating'])+offset)})
        if abs(row['replay_error_m']) > 1e-8:
            raise ValueError('Original forecast not reproduced')
        rows.append(row)
    with (out/'attribution.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    result = {'forecast_issue_sha256': issue['sha256'], 'recorded_at': issue['recorded_at'],
              'reference_at': packet['reference_at'], 'rows': rows, 'verified_blobs': verified,
              'water_balance_max_error_mm': max_balance,
              'maximum_level_replay_error_m': max(abs(r['replay_error_m']) for r in rows),
              'original_local_state_reproduced': True, 'new_forecast_issued': False,
              'model_promoted': False, 'goal_achieved': False,
              'interpretation': 'Additive partition is in flow only, not level. History may contain carried/revised readings. Modeled kernel weight is reliance on forecast inputs, not probability. Persistence and zero future local rain are diagnostic sensitivities, not bounds or accuracy evidence. Future rainfall over upstream basins is not removed by the local-rain sensitivity.'}
    (out/'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    (code/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'output': str(out), 'max_replay_error_m': result['maximum_level_replay_error_m'], 'last': rows[-1]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--ledger', type=Path, default=DEFAULT)
    args = parser.parse_args(); run(args.packet, args.output, args.ledger)
