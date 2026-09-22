"""Read-only development diagnostic of frozen delay-profile predictions."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/experimento-radar-idade-ancora-20260922'
PARENT = ROOT / 'outputs/experimento-radar-mistura-atrasos-20260922'
OUT = ROOT / 'outputs/diagnostico-radar-tendencia-atrasos-20260922'
FAMILIES = ('profile_A_control', 'profile_B_control', 'mixed_profile_candidate', 'age_mixed_candidate')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def save(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def direction(values, threshold):
    return np.where(~np.isfinite(values), 'unknown', np.where(values >= threshold, 'rising', np.where(values <= -threshold, 'falling', 'stable')))


def main():
    assert not OUT.exists(), 'Do not overwrite completed or partial evidence.'
    paths = [Path(__file__), SOURCE / 'predictions.csv', SOURCE / 'evaluation.csv',
             SOURCE / 'artifact-hashes.json', PARENT / 'prepared-inputs.npz',
             PARENT / 'training-masks.npz', PARENT / 'artifact-hashes.json',
             ROOT / 'scripts/hydro_latency_forecast.py']
    for folder in (SOURCE, PARENT):
        for item in json.loads((folder / 'artifact-hashes.json').read_text()):
            assert sha(folder / item['file']) == item['sha256']
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    OUT.mkdir()
    dump(OUT / 'diagnostic-plan.json', dict(
        registered_at_utc=datetime.now(timezone.utc).isoformat(), input_sha256=hashes,
        purpose='Diagnose frozen predictions before choosing another experiment; all periods already known development.',
        partitions=dict(known_trend='Muçum column2 dH1: rising >=0.10 m/h, falling <=-0.10 m/h, stable otherwise, unknown if missing. Nominal-hour rate, not actual elapsed measurement time.',
                        future_response='actual minus profile base: rising >=0.50m, falling <=-0.50m, stable otherwise, unknown if either missing. Diagnostic label only, never model input.',
                        training_response_support='actual minus profile base compared with min/max training response for the same family/fold/horizon; below, within (inclusive), above, unknown. Descriptive univariate support only.'),
        scope='Both profiles, both folds, all12 nominal horizons, all four families, all/observed>=7m. Missing truth retained separately; missing forecasts remain failures in observed denominators. Profiles are alternative views, not independent samples.',
        new_fits=0, tuning=False, promotion=False, independent_test=False, goal_achieved=False))
    data = dict(np.load(PARENT / 'prepared-inputs.npz'))
    masks = dict(np.load(PARENT / 'training-masks.npz'))
    t, truth = data['times'], data['truth']
    rows = list(csv.DictReader((SOURCE / 'predictions.csv').open()))
    groups = defaultdict(list)
    for r in rows:
        groups[r['phase'], r['profile'], int(r['nominal_lead_h'])].append(r)
    reference = {(r['phase'], r['profile'], int(r['horizon_h']), r['family'], r['subset']): r
                 for r in csv.DictReader((SOURCE / 'evaluation.csv').open()) if r['population'] == 'full_schedule'}
    mixedbase = np.where(data['assignment'] == 0, data['base_A'], data['base_B'])
    bases = dict(profile_A_control=data['base_A'], profile_B_control=data['base_B'], mixed_profile_candidate=mixedbase, age_mixed_candidate=mixedbase)
    supports = {}
    training = []
    for phase in ('validation', 'test'):
        for h in range(1, 13):
            target = np.full_like(truth, np.nan)
            target[:-h] = truth[h:]
            mask = masks[f'{phase}_h{h}']
            for family in FAMILIES:
                response = target[mask] - bases[family][mask]
                assert np.isfinite(response).all()
                lo, hi = float(response.min()), float(response.max())
                supports[phase, h, family] = (lo, hi)
                training.append(dict(phase=phase, horizon_h=h, family=family, rows=int(mask.sum()), response_min_m=lo, response_max_m=hi))
    metrics, transitions, extremes = [], [], []
    checks = 0
    for (phase, profile, h), group in sorted(groups.items()):
        times = np.array([datetime.fromisoformat(r['origin']).timestamp() for r in group])
        ix = np.searchsorted(t, times)
        np.testing.assert_array_equal(t[ix], times)
        actual = np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in group])
        base = np.array([float(r['base_m']) if r['base_m'] else np.nan for r in group])
        np.testing.assert_array_equal(base, data[f'base_{profile}'][ix])
        np.testing.assert_array_equal(actual, truth[ix + h])
        response = actual - base
        trend = data[f'features_{profile}'][ix, 2]
        labels = dict(known_trend=direction(trend, .10), future_response=direction(response, .50))
        predictions = {f: np.array([float(r[f + '_m']) if r[f + '_m'] else np.nan for r in group]) for f in FAMILIES}
        for subset in ('all', 'level_ge_7m'):
            pop = np.ones(len(group), dtype=bool) if subset == 'all' else ((actual >= 7) | ~np.isfinite(actual))
            observed = np.isfinite(actual) & pop
            for family, predicted in predictions.items():
                lo, hi = supports[phase, h, family]
                support = np.where(~np.isfinite(response), 'unknown', np.where(response < lo, 'below', np.where(response > hi, 'above', 'within')))
                for partition, label in {**labels, 'training_response_support': support}.items():
                    cats = ('rising', 'falling', 'stable', 'unknown') if partition != 'training_response_support' else ('below', 'within', 'above', 'unknown')
                    start = len(metrics)
                    for cat in cats:
                        selected = pop & (label == cat)
                        obs = observed & selected
                        paired = obs & np.isfinite(predicted)
                        error = predicted[paired] - actual[paired]
                        ae = abs(error)
                        hits = int((ae <= .50).sum())
                        metrics.append(dict(phase=phase, profile=profile, horizon_h=h, family=family, subset=subset, partition=partition, category=cat,
                            classified_rows=int(selected.sum()), unknown_truth=int((selected & ~np.isfinite(actual)).sum()), observed_targets=int(obs.sum()), pairs=int(paired.sum()), failures=int(obs.sum()-paired.sum()), hits=hits,
                            observed_hit_fraction=hits/int(obs.sum()) if obs.any() else None, sum_abs_error_m=float(ae.sum()), sum_error_m=float(error.sum()),
                            mae_m=float(ae.mean()) if len(ae) else None, bias_m=float(error.mean()) if len(ae) else None, max_abs_m=float(ae.max()) if len(ae) else None,
                            under_by_more_than_0_5m=int((error < -.50).sum()), over_by_more_than_0_5m=int((error > .50).sum())))
                    ref = reference[phase, profile, h, family, subset]
                    for field in ('observed_targets', 'pairs', 'failures', 'hits'):
                        assert sum(r[field] for r in metrics[start:]) == int(ref[field])
                        checks += 1
                    assert sum(r['unknown_truth'] for r in metrics[start:]) == int(ref['missing_truth'])
                    assert sum(r['classified_rows'] for r in metrics[start:]) == int(pop.sum())
                    checks += 2
                    paired_count = int(ref['pairs'])
                    if paired_count:
                        np.testing.assert_allclose(sum(r['sum_abs_error_m'] for r in metrics[start:])/paired_count, float(ref['mae_m']), rtol=0, atol=1e-12)
                        np.testing.assert_allclose(sum(r['sum_error_m'] for r in metrics[start:])/paired_count, float(ref['bias_m']), rtol=0, atol=1e-12)
                        checks += 2
            old, new = predictions['mixed_profile_candidate'], predictions['age_mixed_candidate']
            paired = observed & np.isfinite(old) & np.isfinite(new)
            oldhit, newhit = abs(old-actual) <= .5, abs(new-actual) <= .5
            for partition, label in labels.items():
                for cat in ('rising', 'falling', 'stable', 'unknown'):
                    mask = paired & (label == cat)
                    gained = mask & ~oldhit & newhit
                    lost = mask & oldhit & ~newhit
                    transitions.append(dict(phase=phase, profile=profile, horizon_h=h, subset=subset, partition=partition, category=cat,
                        pairs=int(mask.sum()), gained=int(gained.sum()), lost=int(lost.sum()), both_hit=int((mask&oldhit&newhit).sum()), both_miss=int((mask&~oldhit&~newhit).sum()),
                        net_hits=int(gained.sum()-lost.sum())))
        # Largest errors are inspection cases, not a selected evaluation subset.
        for family, predicted in predictions.items():
            valid = np.flatnonzero(np.isfinite(actual) & np.isfinite(predicted))
            largest = valid[np.argsort(-abs(predicted[valid]-actual[valid]), kind='stable')[:5]]
            for rank, j in enumerate(largest, 1):
                lo, hi = supports[phase, h, family]
                extremes.append(dict(phase=phase, profile=profile, horizon_h=h, family=family, rank=rank, origin=group[j]['origin'], target_time=group[j]['target_time'],
                    base_m=float(base[j]), actual_m=float(actual[j]), predicted_m=float(predicted[j]), error_m=float(predicted[j]-actual[j]),
                    dH1_m_per_nominal_hour=float(trend[j]) if np.isfinite(trend[j]) else None, known_trend=labels['known_trend'][j], future_response=labels['future_response'][j],
                    target_response_m=float(response[j]), training_response_min_m=lo, training_response_max_m=hi))
    assert len(metrics) == 4608 and len(transitions) == 768 and len(training) == 96 and len(extremes) == 960
    save(OUT/'strata.csv', metrics)
    save(OUT/'age-hit-transitions.csv', transitions)
    save(OUT/'training-response-support.csv', training)
    save(OUT/'largest-errors.csv', extremes)
    for path, digest in hashes.items():
        assert sha(ROOT/path) == digest
    (OUT/'code.py').write_bytes(Path(__file__).read_bytes())
    dump(OUT/'diagnostic.json', dict(finished_at_utc=datetime.now(timezone.utc).isoformat(), input_sha256=hashes,
        profile_rows=len(rows), distinct_origin_horizon_rows=len(rows)//2, metrics=len(metrics), transitions=len(transitions), reconciliations=checks,
        training_support_rows=len(training), largest_error_cases=len(extremes), new_fits=0, independent_test=False, promoted=False, goal_achieved=False))
    dump(OUT/'artifact-hashes.json', [dict(file=p.name, sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file()])
    print(json.dumps(dict(output=str(OUT), metrics=len(metrics), reconciliations=checks)))


if __name__ == '__main__':
    main()
