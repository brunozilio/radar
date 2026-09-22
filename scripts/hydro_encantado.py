"""Independent six-hour city models, using only observed upstream/local levels.

No Muçum forecast or gauge-datum conversion is used. Historical receipt times
are unavailable: delayed hindcasts stress availability, not a prospective test.
"""
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np

from hydro_history import ana_rows, stamp, TZ

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = 'radar_encantado_v1'
VERSION = 'encantado-6h-v1'
STATIONS = ('86720000', '86510000')
MODEL_CONFIGS = {
    'encantado': {'label': 'Encantado', 'version': VERSION, 'model_id': MODEL_ID, 'codes': STATIONS},
    'santa-tereza': {'label': 'Santa Tereza', 'version': 'santa-tereza-6h-v1',
                     'model_id': 'radar_santa_tereza_v1', 'codes': ('86472600', '86472000')},
}
LAGS = (.5, 1, 2, 4, 8)
MAX_AGE = 90 * 60
FEATURE_NAMES = [f'{code}:{name}' for code in STATIONS
                 for name in ['level', 'age_hours', *[f'change_{h}h' for h in LAGS]]]


def feature_names(stations):
    return [f'{code}:{name}' for code in stations
            for name in ['level', 'age_hours', *[f'change_{h}h' for h in LAGS]]]


def read_levels(path, code, received):
    rows, _ = ana_rows(path, code, received)
    times = np.array(sorted(rows))
    levels = np.array([rows[t][0] for t in times])
    return {'times': times, 'level': levels}


def sample(series, times, max_age=MAX_AGE):
    valid = np.isfinite(series['level'])
    source_times, values = series['times'][valid], series['level'][valid]
    result = np.full(len(times), np.nan)
    ages = np.full(len(times), np.nan)
    if len(source_times):
        indices = np.searchsorted(source_times, times, side='right') - 1
        age = times - source_times[np.maximum(indices, 0)]
        good = (indices >= 0) & (age >= 0) & (age <= max_age)
        result[good] = values[indices[good]]
        ages[good] = age[good]
    return result, ages


def features(series, origins, delays=(0, 0), stations=STATIONS):
    columns = []
    anchors = []
    if len(stations) != len(delays):
        raise ValueError('Station and delay counts differ')
    for code, delay in zip(stations, delays):
        cutoff = origins - delay
        level, age = sample(series[code], cutoff)
        actual_age = age + delay
        level = np.where(actual_age <= MAX_AGE, level, np.nan)
        columns.extend([level, actual_age / 3600])
        anchors.append(level)
        # Lags are relative to the actual anchor timestamp, never to future data.
        for hours in LAGS:
            past, _ = sample(series[code], cutoff - age - hours * 3600)
            columns.append((level - past) / hours)
    return np.column_stack(columns), anchors[0]


def predict(series, reference, model_dir=None, station='encantado'):
    config = MODEL_CONFIGS[station]
    stations = config['codes']
    model_dir = model_dir or ROOT / 'model-artifacts' / config['version']
    spec = json.loads((model_dir / 'model.json').read_text())
    if (spec['id'] != config['version'] or spec['station'] != stations[0] or
            spec['features'] != feature_names(stations) or not spec['validationPassed']):
        raise ValueError('Invalid station model specification')
    X, anchor = features(series, np.array([reference.timestamp()]), stations=stations)
    if not np.isfinite(X).all():
        raise ValueError('Station observations missing, stale or incomplete')
    for i, code in enumerate(stations):
        low, high = spec['levelRange'][code]
        if not low <= X[0, i * 7] <= high:
            raise ValueError('Observed level outside station model training range')
    points = []
    for lead in range(1, 7):
        path = model_dir / f'forecast-{lead}.joblib'
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec['artifacts'][path.name]:
            raise ValueError('Station model integrity failure')
        value = float(joblib.load(path).predict(X)[0] + anchor[0])
        if not np.isfinite(value) or value < 0:
            raise ValueError('Invalid station prediction')
        points.append({'timestamp': (reference + timedelta(hours=lead)).isoformat(), 'level': value})
    observed_at = reference - timedelta(hours=float(X[0, 1]))
    return {'schema': 1, 'station': station, 'generatedAt': datetime.now(TZ).isoformat(),
            'referenceAt': reference.isoformat(), 'experimental': True,
            'intervalMinutes': 15, 'horizonHours': 6, 'modelVersion': config['version'],
            'observation': {'timestamp': observed_at.isoformat(), 'level': float(anchor[0])},
            'models': [{'id': config['model_id'], 'label': f'Modelo de previsão de {config["label"]}', 'points': points}]}


def calculate(out, reference, station='encantado'):
    if station == 'santa-tereza':
        # Both sources already belong to the required, receipt-checked collection.
        received = datetime.now(TZ).timestamp()
        series = {code: read_levels(out / 'raw' / f'ana-{code}-fresh.xml', code, received)
                  for code in MODEL_CONFIGS[station]['codes']}
        result = predict(series, reference, station=station)
        if stamp(result['models'][0]['points'][0]['timestamp']) <= stamp(result['generatedAt']):
            raise ValueError('Santa Tereza target elapsed during calculation')
        return result
    if station != 'encantado':
        raise ValueError('Unknown station')
    now = datetime.now(TZ)
    query = urllib.parse.urlencode({'codEstacao': STATIONS[0],
                                   'dataInicio': (now - timedelta(days=3)).strftime('%d/%m/%Y'),
                                   'dataFim': now.strftime('%d/%m/%Y')})
    url = 'https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais?' + query
    request = urllib.request.Request(url, headers={'User-Agent': 'Radar-public-research/1.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=40) as response:
        body = response.read()
    path = out / 'raw' / f'ana-{STATIONS[0]}-fresh.xml'
    path.write_bytes(body)
    received = datetime.now(TZ)
    receipt = {'url': url, 'station': STATIONS[0], 'collected_at': received.isoformat(),
               'sha256': hashlib.sha256(body).hexdigest(), 'modelVersion': VERSION}
    (out / 'raw' / 'encantado-receipt.json').write_text(json.dumps(receipt, indent=2))
    series = {code: read_levels(out / 'raw' / f'ana-{code}-fresh.xml', code, received.timestamp())
              for code in STATIONS}
    result = predict(series, reference)
    if stamp(result['models'][0]['points'][0]['timestamp']) <= stamp(result['generatedAt']):
        raise ValueError('Encantado target elapsed during calculation')
    return result
