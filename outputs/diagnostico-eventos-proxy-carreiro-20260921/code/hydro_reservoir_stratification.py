"""Diagnostic error slices using only past level endpoints for trend labels."""
import argparse, csv, hashlib, json, math
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from hydro_hourly_forecast import ROOT, BASE, epoch, iso, dump
from hydro_flood_events import inventory, stamp
from hydro_reservoir_mucum_experiment import score
from hydro_upstream_audit import savecsv


def origin_trend(origin, observations, frozen):
    anchor = origin-900; previous = anchor-3*3600
    values = []
    for at in [anchor, previous]:
        row = observations.get(at)
        if row is None or row['quality'] != 'Dado aprovado' or row['level_m'] is None:
            return 'unknown', None
        value = frozen.get(at, np.nan)
        if not np.isfinite(value) or abs(value-row['level_m']) > 1e-8:
            return 'unknown', None
        values.append(value)
    slope = (values[0]-values[1])/3
    if math.isclose(abs(slope), .05, rel_tol=0, abs_tol=1e-12):
        return 'stable', slope
    return ('rising' if slope > .05 else 'falling' if slope < -.05 else 'stable'), slope


def load_sources(paths):
    latest = {}
    for path in paths:
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        for _, el in ET.iterparse(path, events=['end']):
            if el.tag.split('}')[-1] != 'DadosHidrometereologicos':
                continue
            row = {x.tag.split('}')[-1]: x.text for x in el}; at = epoch(row['DataHora'])
            if row.get('CodEstacao') != '86510000': raise ValueError('Wrong station')
            try: level = float(row['NivelFinal'])/100
            except (TypeError, ValueError): level = None
            if level is not None and (not math.isfinite(level) or level < 0): level = None
            latest[at] = {'level_m': level, 'quality': row.get('CQ_NivelFinal'),
                          'timezone_verified': False, 'datum_verified': False,
                          'source_path': str(path.resolve()), 'source_sha256': source_hash}
            el.clear()
    return latest


def verify_prediction_hash(path, manifest):
    expected = manifest.get(path.name) if isinstance(manifest, dict) else next(
        (r['sha256'] for r in manifest if r['file'] == path.name), None)
    if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Missing or mismatched prediction hash: '+str(path))


def run(out, policy_path):
    policy = json.loads(policy_path.read_text()); source = ROOT/policy['prediction_source']
    raw = ROOT/'outputs/mucum-propagacao-2026-09-21/raw'
    xml = [raw/'ana-86510000-2025.xml', raw/'ana-86510000.xml', raw/'ana-86510000-latest.xml', BASE/'raw/ana-86510000-fresh.xml']
    observations = load_sources(xml); z = dict(np.load(BASE/'telemetria-latencia.npz'))
    frozen = dict(zip(z['times'], z['raw:86510000:H']))
    event_policy_path = ROOT/'docs/flood-event-grouping-policy.json'
    event_policy = json.loads(event_policy_path.read_text())
    datum = 'historical-published-gauge-reference-unverified'
    event_input = {('86510000', datum, stamp(iso(at))): (row, row['source_sha256']) for at, row in observations.items()}
    events, membership = inventory(event_input, event_policy)
    manifest = json.loads((source/'artifact-hashes.json').read_text())
    prediction_path = source/'predictions.csv'
    verify_prediction_hash(prediction_path, manifest)
    predictions = []; mismatch = 0; target_unknown_quality = 0
    for r in csv.DictReader(prediction_path.open()):
        at = epoch(r['origin']); target = epoch(r['target_time'])
        trend, slope = origin_trend(at, observations, frozen)
        row = {**r, 'actual_m': float(r['actual_m']) if r['actual_m'] else None,
               'reference_m': float(r['reference_m']) if r['reference_m'] else None,
               'julho_levels_m': float(r['julho_levels_m']) if r['julho_levels_m'] else None,
               'origin_trend': trend, 'net_slope_3h_m_per_h': slope}
        actual_source = observations.get(target)
        agrees = actual_source and row['actual_m'] is not None and actual_source['level_m'] is not None and abs(actual_source['level_m']-row['actual_m']) < 1e-8
        if row['actual_m'] is not None and not agrees: mismatch += 1
        if row['actual_m'] is not None and (not actual_source or actual_source['quality'] != 'Dado aprovado'): target_unknown_quality += 1
        row['target_explicitly_approved_and_matching'] = bool(agrees and actual_source['quality'] == 'Dado aprovado')
        row['observed_cluster_id'] = membership.get(('86510000', datum, stamp(r['target_time'])), '') if row['target_explicitly_approved_and_matching'] else ''
        predictions.append(row)
    strata = []
    for h in range(1, 13):
        for trend in ['rising', 'falling', 'stable', 'unknown']:
            selected = [r for r in predictions if int(r['nominal_lead_h']) == h and r['origin_trend'] == trend]
            for high in [False, True]:
                strata.extend([{'nominal_lead_h': h, 'origin_trend': trend, **r} for r in score(selected, high)])
    represented = {r['observed_cluster_id'] for r in predictions if r['observed_cluster_id']}
    clusters = [e for e in events if e['event_id'] in represented]; by_event = []
    for event in clusters:
        for h in range(1, 13):
            selected = [r for r in predictions if r['observed_cluster_id'] == event['event_id'] and int(r['nominal_lead_h']) == h]
            by_event.extend([{'observed_cluster_id': event['event_id'], 'nominal_lead_h': h,
                              'first_exceedance_at': event['first_exceedance_at'],
                              'complete_observed_cluster': event['complete_observed_cluster'],
                              'independence_certified': False, **r} for r in score(selected, True)])
    out.mkdir(parents=True, exist_ok=False)
    (out/'policy.json').write_bytes(policy_path.read_bytes())
    for name, rows in [('predictions-with-labels', predictions), ('trend-metrics', strata), ('cluster-metrics', by_event)]: savecsv(out/f'{name}.csv', rows)
    paths = xml+[BASE/'telemetria-latencia.npz', prediction_path, source/'artifact-hashes.json', event_policy_path, policy_path, Path(__file__), ROOT/'scripts/hydro_flood_events.py', ROOT/'scripts/hydro_reservoir_mucum_experiment.py', ROOT/'scripts/hydro_hourly_forecast.py']
    dump(out/'observed-clusters.json', {'represented_clusters': clusters, 'all_historical_clusters': events,
                                     'independent_events_certified': 0, 'input_policy': event_policy})
    dump(out/'audit.json', {'input_sha256': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                          'pairs': len(predictions), 'target_value_mismatches_against_latest_source': mismatch,
                          'target_rows_without_explicit_approved_qc': target_unknown_quality,
                          'trend_row_counts': dict(Counter(r['origin_trend'] for r in predictions)),
                          'represented_observed_clusters': len(clusters), 'historical_only': True,
                          'promoted': False, 'live_issuance': False, 'goal_achieved': False})
    (out/'code').mkdir()
    for path in paths:
        if path.suffix == '.py': (out/'code'/path.name).write_bytes(path.read_bytes())
    print(json.dumps({'output': str(out), 'clusters': len(clusters), 'target_mismatches': mismatch, 'target_unapproved': target_unknown_quality}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--policy', type=Path, default=ROOT/'docs/reservoir-candidate-stratification-policy.json')
    a = p.parse_args(); run(a.output, a.policy)
