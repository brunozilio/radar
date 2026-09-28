"""Exploratory rain/level response associations; never a routing-time estimate.

Select a lag only in training, then report the same lag in later partitions.
Uses an existing audited rain-window matrix, with its historical QC/receipt
limitations explicitly retained, and new exact-hour Muçum observations.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from hydro_propagation_model import epoch, iso, shift

GROUPS = ('Baixo Antas', 'Carreiro', 'Prata-Turvo', 'Alto Antas', 'Tainhas')
PLAN = dict(schema='radar-rain-response-lags/v1', reference='End of 3h Muçum level change',
            predictor='Area-weighted observed 3h rain ending lag hours before reference',
            lagsHours=list(range(49)), minimumPairs=96, minimumWetPairs=24,
            minimumRegionalCoverage=.5, responseHours=3,
            selection='Largest positive Pearson correlation of rain with level change, training only; ties prefer smaller lag',
            trainingEnd='2025-10-01T00:00:00-03:00', validationEnd='2026-07-01T00:00:00-03:00',
            testEnd='2026-09-21T00:00:00-03:00', embargoHours=54,
            useForForecast=False, physicalTravelTimeClaim=False,
            limitations=['Rain matrix is a previously audited historical derivative, not as-received prospective evidence.',
                         'Shared storms, reservoirs and unmeasured contributions confound association.',
                         'Coverage is not an uncertainty interval; no rain source is replaced by zero here.',
                         'Previously inspected chronological periods are development diagnostics.'])


def correlation(x, y, mask):
    valid = mask & np.isfinite(x) & np.isfinite(y)
    wet = valid & (x > .1)
    value = None
    if valid.sum() >= PLAN['minimumPairs'] and wet.sum() >= PLAN['minimumWetPairs']:
        if np.std(x[valid]) > 1e-12 and np.std(y[valid]) > 1e-12:
            value = float(np.corrcoef(x[valid], y[valid])[0, 1])
    return dict(pairs=int(valid.sum()), wetPairs=int(wet.sum()), correlation=value)


def evaluate(times, levels, rain, *, plan=PLAN):
    response = levels - shift(levels, plan['responseHours'])
    train, validation, test = map(epoch, (plan['trainingEnd'], plan['validationEnd'], plan['testEnd']))
    embargo = plan['embargoHours'] * 3600
    masks = dict(train=times < train, validation=(times >= train+embargo) & (times < validation),
                 test=(times >= validation+embargo) & (times < test), stress_current=times >= test)
    midpoint = (float(times[0])+train)/2
    masks.update(train_first=(times < midpoint), train_second=(times >= midpoint) & (times < train))
    rows, selected = [], {}
    for region, values in rain.items():
        options = []
        for lag in plan['lagsHours']:
            delayed = shift(values, lag)
            score = correlation(delayed, response, masks['train'])
            row = dict(region=region, lagHours=lag, **score)
            rows.append(row)
            if score['correlation'] is not None and score['correlation'] > 0:
                options.append(row)
        if not options:
            selected[region] = dict(status='unsupported', lagHours=None)
            continue
        chosen = max(options, key=lambda row: (row['correlation'], -row['lagHours']))
        lag = chosen['lagHours']
        plateau = [r['lagHours'] for r in options if r['correlation'] >= chosen['correlation']*.95]
        selected[region] = dict(status='exploratory_association', lagHours=lag,
            trainingPlateauWithin5PercentHours=plateau,
            sameFrozenLagByPeriod={phase: correlation(shift(values, lag), response, mask) for phase, mask in masks.items()})
    return dict(plan=plan, selected=selected, allTrainingLagScores=rows,
                interpretation='Diagnostic statistical lags only; neither fitted forecast inputs nor hydraulic travel times.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--levels', type=Path, required=True)
    parser.add_argument('--rain', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.levels, args.rain, Path(__file__))}
    # Seal the fixed plan and source versions before examining correlations.
    (args.output/'plan.json').write_text(json.dumps(dict(plan=PLAN, sourceSha256=sources), indent=2)+'\n')
    level_data, rain_data = np.load(args.levels), np.load(args.rain)
    times = level_data['times']
    lookup = {t:i for i,t in enumerate(rain_data['times'])}
    rain = {}
    for group in GROUPS:
        values = np.full(len(times), np.nan)
        for i, at in enumerate(times):
            j = lookup.get(at)
            if j is not None and rain_data[group+':cover3'][j] >= .5:
                values[i] = rain_data[group+':rain3'][j]
        rain[group] = values
    result = evaluate(times, level_data['86510000:H'], rain)
    result['sourceSha256'] = sources
    result['range'] = dict(start=iso(times[0]), end=iso(times[-1]))
    (args.output/'report.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps(result['selected'], indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
