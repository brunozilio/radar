"""Fail closed on incomplete, mismatched-hour inputs before any model runs."""
import json
from datetime import datetime, timedelta
import numpy as np
from hydro_history import ana_rows, ceran_rows, sha, stamp, TZ
from hydro_rain_windows import observed_rain_windows

LEVELS = ('86510000', '86472000', '86472600', '86500000')
PLANTS = ('julho', 'monte', 'castro')
GROUPS = ('Baixo Antas', 'Carreiro', 'Prata-Turvo', 'Alto Antas', 'Tainhas')
MAX_REFERENCE_AGE_HOURS = 3


class InputsNotReady(ValueError):
    def __init__(self, report):
        self.report = report
        super().__init__('Inputs not ready: ' + '; '.join(report['missing']))


def require_features(values):
    missing = np.flatnonzero(~np.isfinite(values)).tolist()
    if missing:
        raise InputsNotReady({'status': 'waiting_for_data', 'missing': [f'Missing model feature columns: {missing}']})


def evaluate(out, reference, weights_path, now=None):
    now = now or datetime.now(TZ)
    if reference.tzinfo is None or reference.minute or reference.second or reference.microsecond or reference > now:
        raise ValueError('Reference must be a past or current exact, timezone-aware hour')
    ref = reference.timestamp()
    groups = json.loads(weights_path.read_text())
    if [g['group'] for g in groups] != list(GROUPS):
        raise ValueError('Unexpected rainfall regions')
    codes = sorted(set(LEVELS) | {c for g in groups for c in g['weights']})
    manifest = json.loads((out / 'collection-manifest.json').read_text())
    sources = {r['file']: r for r in manifest}
    missing, levels, flows, rain = [], {}, {}, {}
    unavailable_rain_sources = {}

    def source(name, required=True):
        item = sources.get(name)
        path = out / 'raw' / name
        def unavailable(reason):
            message = f'{name}: {reason}'
            if required:
                missing.append(message)
            else:
                unavailable_rain_sources[name] = reason
            return None
        # An optional transport failure is not permission to accept a tampered
        # body. Validate any retained body even if its manifest reports failure.
        if item and path.is_file() and sha(path) != item.get('sha256'):
            raise ValueError(f'{name}: source integrity failure')
        if not item or 'error' in item or not path.is_file():
            return unavailable('source unavailable')
        received = stamp(item['collected_at'])
        if not 0 <= now.timestamp() - received <= 3600:
            return unavailable('collection stale or future')
        return path, received

    for code in codes:
        receipt = source(f'ana-{code}-fresh.xml', required=code in LEVELS)
        if not receipt:
            continue
        try:
            rows, _ = ana_rows(receipt[0], code, min(receipt[1], now.timestamp()), strict_quality=True)
        except ValueError as exc:
            missing.append(f'{code}: {exc}')
            continue
        times = np.array(sorted(t for t in rows if t <= ref))
        if code in LEVELS:
            value = rows.get(ref, [np.nan])[0]
            levels[code] = float(value) if np.isfinite(value) else None
            if not np.isfinite(value):
                missing.append(f'{code}: approved river level missing at {reference.isoformat()}')
        # Only complete measured intervals ending at this reference hour count.
        # A stale gauge contributes no coverage, even if downloaded just now.
        coverage = 0.
        if len(times) >= 2 and times[-1] == ref and np.isfinite(rows[ref][2]):
            values = np.array([rows[t][2] for t in times])
            _, covered = observed_rain_windows(times, values, np.array([ref]), windows=[1])[1]
            coverage = 1. if covered[0] >= 1. - 1e-9 else 0.
        rain[code] = coverage
    for plant in PLANTS:
        receipt = source(f'ceran-{plant}-fresh.html')
        if not receipt:
            continue
        try:
            rows, _ = ceran_rows(*receipt)
            values = rows.get(ref, [np.nan, np.nan])
            flows[plant] = [float(v) if np.isfinite(v) else None for v in values]
            if not np.isfinite(values).all():
                missing.append(f'{plant}: outflow/inflow missing at {reference.isoformat()}')
        except ValueError as exc:
            missing.append(f'{plant}: {exc}')
    coverage = {}
    for group in groups:
        value = sum(w * rain.get(c, 0.) for c, w in group['weights'].items())
        coverage[group['group']] = value
        if value < .5:
            missing.append(f'{group["group"]}: same-hour rain coverage {value:.1%} below 50%')
    for model in ('gfs_seamless', 'ecmwf_ifs025', 'icon_global'):
        source(f'weather-{model}.json')
    return {'status': 'waiting_for_data' if missing else 'ready', 'referenceAt': reference.isoformat(),
            'checkedAt': now.isoformat(), 'missing': missing, 'levels': levels, 'flows': flows,
            'rainCoverage': coverage, 'unavailableRainSources': unavailable_rain_sources,
            'rainPolicy': 'Five regions, each >=50% measured coverage in (H-1h,H], ending at H; zero is valid rain. Unavailable non-level rain gauges contribute zero coverage.'}


def require_ready(out, reference, weights_path):
    report = evaluate(out, reference, weights_path)
    (out / 'input-readiness.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if report['status'] != 'ready':
        raise InputsNotReady(report)
    return report


def select_latest_ready(out, checked_reference, weights_path, *, after_reference=None, now=None):
    """Choose a complete observed hour, without advancing any source timestamp.

    The polling clock is only an upper bound. Every candidate uses its own exact
    hour for all observed inputs. Failed candidates and exclusions are retained.
    """
    now = now or datetime.now(TZ)
    if (checked_reference.tzinfo is None or checked_reference.minute or
            checked_reference.second or checked_reference.microsecond or checked_reference > now):
        raise ValueError('Checked reference must be a current or past exact timezone-aware hour')
    if after_reference is not None and (after_reference.tzinfo is None or
            after_reference.minute or after_reference.second or after_reference.microsecond):
        raise ValueError('Last published reference must be an exact timezone-aware hour')
    selection = {'checkedReferenceAt': checked_reference.isoformat(),
        'checkedAt': now.isoformat(),
        'afterReferenceAt': after_reference.isoformat() if after_reference else None,
        'maximumReferenceAgeHours': MAX_REFERENCE_AGE_HOURS,
        'selectedReferenceAt': None, 'candidates': []}
    selected = None
    latest_missing = []
    for back in range(MAX_REFERENCE_AGE_HOURS + 1):
        reference = checked_reference - timedelta(hours=back)
        age = (now-reference).total_seconds()
        candidate = {'referenceAt': reference.isoformat(), 'referenceAgeSeconds': age}
        if after_reference is not None and reference <= after_reference:
            candidate.update(status='already_published', missing=['Reference is not newer than the last published issue'])
        elif age > MAX_REFERENCE_AGE_HOURS * 3600:
            candidate.update(status='reference_too_old', missing=['Reference age exceeds three hours'])
        else:
            report = evaluate(out, reference, weights_path, now=now)
            candidate.update(report)
            if not latest_missing:
                latest_missing = report['missing']
            if report['status'] == 'ready':
                selected = (reference, report)
                selection['selectedReferenceAt'] = reference.isoformat()
        selection['candidates'].append(candidate)
        if selected is not None:
            break
    (out/'reference-selection.json').write_text(json.dumps(selection, ensure_ascii=False, indent=2)+'\n')
    if selected is None:
        report = {'status':'waiting_for_data', 'referenceAt':checked_reference.isoformat(),
            'checkedReferenceAt':checked_reference.isoformat(), 'checkedAt':now.isoformat(),
            'missing':['No newer complete observation hour within the three-hour age limit', *latest_missing],
            'referenceSelection':selection}
        (out/'input-readiness.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        raise InputsNotReady(report)
    reference, report = selected
    report = {**report, 'checkedReferenceAt':checked_reference.isoformat(), 'referenceSelection':selection}
    (out/'input-readiness.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return reference, report
