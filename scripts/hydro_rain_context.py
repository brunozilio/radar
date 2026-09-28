"""As-of rain evidence for a separate, non-public Muçum forecast candidate.

The hydrometric reference is the last observation hour. Every source body and
receipt must already exist at issuance. Missing/suspect gauge intervals remain
unknown; meteorological point forecasts are never relabelled as measured rain.
"""
from __future__ import annotations

import json
import urllib.parse
from datetime import datetime, timedelta

import numpy as np

from hydro_history import ana_rows, sha, TZ
from hydro_hourly_collect import RAIN_QUERY, RAIN_WEIGHTS
from hydro_rain_windows import observed_rain_windows

WINDOWS = (1, 3, 6, 12, 24)
HORIZON = 6
MODELS = ('gfs_seamless', 'ecmwf_ifs025', 'icon_global')
MAX_RECEIPT_AGE_SECONDS = 3600
MIN_REGION_COVERAGE = .5


def _time(value):
    parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(parsed, datetime) or parsed.tzinfo is None:
        raise ValueError('Timestamp must have a timezone')
    return parsed


def _receipt(out, sources, name, issued):
    row = sources.get(name)
    path = out / 'raw' / name
    if row is None or row.get('error') or not path.is_file():
        raise ValueError('source unavailable')
    if sha(path) != row.get('sha256'):
        raise ValueError('raw body hash mismatch')
    received = _time(row['collected_at'])
    requested = _time(row['requested_at'])
    if requested > received or received > issued:
        raise ValueError('source receipt is after issuance or clock order is invalid')
    if (issued - received).total_seconds() > MAX_RECEIPT_AGE_SECONDS:
        raise ValueError('source receipt is stale')
    return path, row, received


def _weather_points(body, groups, requested_coordinates, reference, issued):
    if not isinstance(body, list) or len(body) != len(groups):
        raise ValueError('expected one point for each frozen region')
    points = {}
    for group, requested, location in zip(groups, requested_coordinates, body):
        try:
            latitude, longitude = float(location['latitude']), float(location['longitude'])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError('missing weather grid coordinates') from exc
        if abs(latitude - requested[0]) > .25 or abs(longitude - requested[1]) > .25:
            raise ValueError(f'{group}: weather grid point does not match requested region')
        if location.get('utc_offset_seconds') != -10800 or location.get('hourly_units', {}).get('precipitation') != 'mm':
            raise ValueError('weather timezone or precipitation units mismatch')
        hourly = location.get('hourly', {})
        times, values = hourly.get('time'), hourly.get('precipitation')
        if not isinstance(times, list) or not isinstance(values, list) or len(times) != len(values):
            raise ValueError('weather time/value shape mismatch')
        lookup = {}
        for at, amount in zip(times, values):
            valid_at = datetime.fromisoformat(at)
            valid_at = valid_at.replace(tzinfo=TZ) if valid_at.tzinfo is None else valid_at.astimezone(TZ)
            if valid_at in lookup:
                raise ValueError('duplicate weather valid hour')
            if amount is not None:
                amount = float(amount)
                if not np.isfinite(amount) or amount < 0 or amount > 500:
                    amount = None
            lookup[valid_at] = amount
        targets = [reference + timedelta(hours=h) for h in range(1, HORIZON + 1)]
        amounts = [lookup.get(target) for target in targets]
        totals = []
        for h in range(1, HORIZON + 1):
            first = amounts[:h]
            totals.append(round(sum(first), 3) if all(value is not None for value in first) else None)
        points[group] = {
            'latitude': latitude, 'longitude': longitude,
            'requestedLatitude': requested[0], 'requestedLongitude': requested[1],
            'futureHourlyMm': amounts, 'futureCumulativeMmByLead': totals,
            'targetTimes': [target.isoformat() for target in targets],
            'targetIsFutureAtIssue': [target > issued for target in targets],
            'spatialRole': 'single sampled grid point; not a catchment area mean',
        }
    return points


def normalize_rain_context(out, reference, issued_at):
    """Return a JSON-ready shadow packet, including explicit missing-data reasons.

    Caller should save the packet before forecasting. `reference` and
    `issued_at` must be timezone-aware; a receipt after issuance is rejected.
    """
    reference, issued = _time(reference), _time(issued_at)
    if reference > issued or reference.minute or reference.second or reference.microsecond:
        raise ValueError('Rain reference must be an exact hour before issuance')
    packet = {
        'schema': 'radar-rain-context-shadow/v1', 'status': 'unavailable',
        'referenceAt': reference.isoformat(), 'issuedAt': issued.isoformat(),
        'shadowOnly': True, 'providerRunTimeVerified': False,
        'observedPolicy': 'ANA ChuvaFinal with CQ_ChuvaFinal=Dado aprovado; measured intervals only; full station window and >=50% regional spatial weight required',
        'forecastPolicy': 'Open-Meteo current forecast sampled at five region centroids; collection receipt proves as-of availability but provider run time is not exposed',
        'regions': {}, 'forecastModels': {}, 'issues': [],
    }
    try:
        weights = json.loads(RAIN_WEIGHTS.read_text())
        groups = [row['group'] for row in weights]
        query = json.loads(RAIN_QUERY.read_text())
        if groups != query['groups']:
            raise ValueError('Rain group order differs from frozen forecast points')
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(query['url']).query)
        latitudes = [float(item) for item in params['latitude'][0].split(',')]
        longitudes = [float(item) for item in params['longitude'][0].split(',')]
        if len(latitudes) != len(groups) or len(longitudes) != len(groups):
            raise ValueError('Rain forecast coordinate count mismatch')
        requested_coordinates = list(zip(latitudes, longitudes))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        packet['issues'].append({'source': 'rain-context-configuration', 'reason': str(exc)})
        return packet
    try:
        rows = json.loads((out / 'collection-manifest.json').read_text())
        sources = {row['file']: row for row in rows}
        if len(sources) != len(rows):
            raise ValueError('duplicate collection manifest source')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        packet['issues'].append({'source': 'collection-manifest.json', 'reason': str(exc)})
        sources = {}
    stations = {}
    for code in sorted({code for region in weights for code in region['weights']}):
        name = f'ana-{code}-fresh.xml'
        try:
            path, receipt, received = _receipt(out, sources, name, issued)
            values, future_excluded = ana_rows(path, code, received.timestamp(), strict_quality=True)
            times = np.array(sorted(t for t in values if t <= reference.timestamp()), dtype=float)
            if len(times) < 2:
                raise ValueError('fewer than two pre-reference gauge timestamps')
            amount = np.array([values[t][2] for t in times], dtype=float)
            windows = observed_rain_windows(times, amount, np.array([reference.timestamp()]), WINDOWS)
            stations[code] = {'receivedAt': received.isoformat(), 'sha256': receipt['sha256'],
                'futureRowsExcluded': future_excluded,
                'windows': {str(h): {'mm': float(windows[h][0][0]), 'temporalCoverage': float(windows[h][1][0])}
                            for h in WINDOWS}}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            stations[code] = {'windows': {}, 'reason': str(exc)}
            packet['issues'].append({'source': name, 'reason': str(exc)})
    for group in weights:
        name = group['group']
        expected_weights = group['weights']
        if not np.isclose(sum(expected_weights.values()), 1., atol=1e-6):
            raise ValueError(f'{name}: invalid fixed spatial weights')
        windows = {}
        for h in WINDOWS:
            good = {code: weight for code, weight in expected_weights.items()
                    if stations[code]['windows'].get(str(h), {}).get('temporalCoverage', 0) >= 1 - 1e-9}
            coverage = float(sum(good.values()))
            value = sum(weight * stations[code]['windows'][str(h)]['mm'] for code, weight in good.items()) / coverage if coverage >= MIN_REGION_COVERAGE else None
            windows[str(h)] = {'mm': round(value, 3) if value is not None else None,
                'spatialCoverage': round(coverage, 6), 'reportingStations': sorted(good),
                'status': 'ready' if value is not None else 'insufficient_coverage'}
        packet['regions'][name] = {'windows': windows, 'areaKm2': group['area_km2']}
    for model in MODELS:
        name = f'weather-{model}.json'
        try:
            path, receipt, received = _receipt(out, sources, name, issued)
            points = _weather_points(json.loads(path.read_text()), groups, requested_coordinates,
                                     reference, issued)
            packet['forecastModels'][model] = {'status': 'ready', 'receivedAt': received.isoformat(),
                'sha256': receipt['sha256'], 'providerRunAt': receipt.get('issued_at'),
                'providerRunTimeVerified': False, 'points': points}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            packet['forecastModels'][model] = {'status': 'unavailable', 'reason': str(exc),
                'providerRunAt': None, 'providerRunTimeVerified': False, 'points': {}}
            packet['issues'].append({'source': name, 'reason': str(exc)})
    observed_ready = all(row['windows']['6']['status'] == 'ready' for row in packet['regions'].values())
    observed_windows_ready = all(window['status'] == 'ready' for row in packet['regions'].values()
                                 for window in row['windows'].values())
    forecast_ready = all(row['status'] == 'ready' and all(
        all(amount is not None for amount in point['futureCumulativeMmByLead'])
        for point in row['points'].values()) for row in packet['forecastModels'].values())
    packet['status'] = 'ready' if observed_windows_ready and forecast_ready else 'partial' if observed_ready or any(
        row['status'] == 'ready' for row in packet['forecastModels'].values()) else 'unavailable'
    packet['observedSixHourCoverageReady'] = observed_ready
    packet['observedAllWindowsReady'] = observed_windows_ready
    packet['forecastSixHourCoverageReady'] = forecast_ready
    return packet
