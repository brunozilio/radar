"""Receipt-aware hydrometric shadow independent of the public rain gate.

No fitting, imputation, summed cascade flows, or public publication. Raw source
receipts remain in the caller's immutable attempt archive.
"""
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from hydro_history import TZ, ana_rows, ceran_rows, stamp
from hydro_propagation_model import predict

LEVELS = ('86510000', '86472000', '86472600', '86500000')
PLANTS = ('julho', 'monte', 'castro')
MODEL_PATH = Path('model-artifacts/mucum-propagation-v1/model.json')
MAX_AGE_SECONDS = 10800
NOWCAST_VERSION = 'mucum-local-nowcast-shadow-v1'


def run_local_nowcast_shadow(out, public_source):
    """Evaluate a receipt-backed local-level recentering without publishing it."""
    result = dict(schema='radar-local-nowcast-shadow/v1', mode='shadow', publishable=False,
                  modelVersion=NOWCAST_VERSION, sourceModelSha256=public_source.get('modelSha256'),
                  status='unavailable', points=[],
                  recipe='docs/nowcast-shadow-2026-09-28.md')
    try:
        if public_source.get('status') != 'calculated':
            raise ValueError('Hydrometric source forecast unavailable')
        reference = stamp(public_source['referenceAt'])
        issued = stamp(public_source['generatedAt'])
        base = float(public_source['observation']['level'])
        points = public_source['points']
        first = points[0]
        first_at = stamp(first['timestamp'])
        if not reference < issued < first_at or not math.isfinite(base):
            raise ValueError('Invalid forecast chronology or anchor')
        source = next(row for row in public_source['sources'] if row['file'] == 'ana-86510000-fresh.xml')
        path = out / 'raw' / source['file']
        body_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if body_sha != source['sha256']:
            raise ValueError('Local observation receipt checksum mismatch')
        received = stamp(source['availableAt'])
        if not 0 <= issued - received <= 3600:
            raise ValueError('Local observation receipt unavailable at issuance')
        observations, _ = ana_rows(path, '86510000', received, strict_quality=True)
        eligible = [(at, float(values[0])) for at, values in observations.items()
                    if reference < at <= issued and issued-at <= 3600 and math.isfinite(values[0])]
        if not eligible:
            raise ValueError('No approved newer local reading available at issuance')
        observed_at, observed_level = max(eligible)
        expected = base + (float(first['level'])-base) * (observed_at-reference)/(first_at-reference)
        correction = max(-.5, min(.5, observed_level-expected))
        if not math.isfinite(expected) or not math.isfinite(correction):
            raise ValueError('Nonfinite nowcast correction')
        result.update(status='calculated', referenceAt=public_source['referenceAt'],
                      generatedAt=public_source['generatedAt'],
                      observation=dict(timestamp=datetime.fromtimestamp(observed_at, TZ).isoformat(),
                                       level=observed_level, receiptSha256=body_sha,
                                       receiptAt=source['availableAt'], quality='Dado aprovado'),
                      modelExpectedAtObservation=expected, correctionMetres=correction,
                      points=[dict(timestamp=point['timestamp'], nominalLeadHours=point['nominalLeadHours'],
                                   originalLevel=float(point['level']), candidateLevel=float(point['level'])+correction)
                              for point in points])
    except Exception as exc:
        # A candidate failure must never block the already validated public issue.
        result['reason'] = f'{type(exc).__name__}: {exc}'
    (out / 'local-nowcast-shadow.json').write_text(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + '\n')
    return result


def load_inputs(out, checked_reference, issued):
    """Exact observed hours only; availability is the actual raw receipt time."""
    if checked_reference.tzinfo is None or checked_reference.timestamp() % 3600:
        raise ValueError('Exact timezone-aware reference required')
    if issued.tzinfo is None or issued < checked_reference:
        raise ValueError('Issue cannot precede polling reference')
    manifest = json.loads((out / 'collection-manifest.json').read_text())
    names = [f'ana-{code}-fresh.xml' for code in LEVELS] + [f'ceran-{plant}-fresh.html' for plant in PLANTS]
    by_name = {}
    for row in manifest:
        if row.get('file') in names:
            if row['file'] in by_name:
                raise ValueError('Duplicate required source receipt')
            by_name[row['file']] = row
    times = np.arange(checked_reference.timestamp() - 72 * 3600,
                      checked_reference.timestamp() + 1, 3600, dtype=float)
    positions = {t: i for i, t in enumerate(times)}
    data, sources, missing = {}, [], []
    for name in names:
        row = by_name.get(name)
        path = out / 'raw' / name
        if not row or row.get('error') or not path.is_file():
            missing.append(f'{name}: source unavailable')
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != row.get('sha256'):
            raise ValueError(f'{name}: receipt checksum mismatch')
        received_at = datetime.fromisoformat(row['collected_at'].replace('Z', '+00:00'))
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise ValueError(f'{name}: receipt timezone required')
        received = received_at.timestamp()
        if not 0 <= issued.timestamp() - received <= 3600:
            missing.append(f'{name}: stale or future receipt')
            continue
        if name.startswith('ana-'):
            source = name.split('-')[1]
            observations, _ = ana_rows(path, source, received, strict_quality=True)
            values = {source + ':H': 0}
            quality = 'Dado aprovado'
        else:
            source = name.split('-')[1]
            observations, _ = ceran_rows(path, received)
            values = {source + ':Q': 0, source + ':I': 1}
            quality = 'CERAN as reported; no independent instrument certification'
        for key, column in values.items():
            series = np.full(len(times), np.nan)
            for observed_at, fields in observations.items():
                if observed_at in positions:
                    series[positions[observed_at]] = fields[column]
            data[key] = series
        sources.append(dict(file=name, source=source, availableAt=row['collected_at'],
                            sha256=sha, quality=quality, keys=list(values)))
    if missing:
        raise ValueError('; '.join(missing))
    return times, data, sources


def run_shadow(out, root, checked_reference, *, now=None):
    """Always record success/unavailability; shadow failure never unlocks baseline."""
    issued = now or datetime.now(TZ)
    result = dict(schema='radar-propagation-shadow/v1', mode='shadow', publishable=False,
                  station='86510000', checkedReferenceAt=checked_reference.isoformat(),
                  generatedAt=issued.isoformat(), status='unavailable', points=[], candidates=[],
                  limitations=[
                      'Statistical response lags are not physical water travel times.',
                      'Historical fit does not certify historical availability or prospective accuracy.',
                      'Forecast accuracy remains experimental; prospective accuracy has not been established.'])
    try:
        body = (root / MODEL_PATH).read_bytes()
        model_sha = hashlib.sha256(body).hexdigest()
        if (root / 'manifest.json').is_file():
            runtime = json.loads((root / 'manifest.json').read_text())
            if runtime.get(str(MODEL_PATH)) != model_sha:
                raise ValueError('Propagation model runtime checksum mismatch')
        model = json.loads(body)
        result['modelSha256'] = model_sha
        times, data, sources = load_inputs(out, checked_reference, issued)
        result['sources'] = sources
        for back in range(4):
            reference = checked_reference - timedelta(hours=back)
            if not 0 <= (issued - reference).total_seconds() <= MAX_AGE_SECONDS:
                result['candidates'].append(dict(referenceAt=reference.isoformat(), reason='Reference older than three hours'))
                continue
            try:
                candidate = predict(model, times, data, reference_at=reference.isoformat(), issued_at=issued.isoformat())
            except ValueError as exc:
                result['candidates'].append(dict(referenceAt=reference.isoformat(), reason=str(exc)))
                continue
            generated = now or datetime.now(TZ)
            if (generated-reference).total_seconds() > MAX_AGE_SECONDS:
                continue
            if any(not 0 <= generated.timestamp()-stamp(source['availableAt']) <= 3600 for source in sources):
                raise ValueError('Source receipt exceeded the freshness limit during inference')
            points = [dict(point, realLeadHours=(stamp(point['timestamp'])-generated.timestamp())/3600)
                      for point in candidate['points'] if stamp(point['timestamp']) > generated.timestamp()]
            if not points:
                continue
            result.update(status='calculated', referenceAt=reference.isoformat(),
                          generatedAt=generated.isoformat(), points=points,
                          observation=candidate['observation'],
                          modelVersion=candidate.get('modelVersion', model.get('version')),
                          contract=candidate.get('contract'), rainRequired=False,
                          horizonHours=6, forecastStartLeadHours=points[0]['nominalLeadHours'],
                          extrapolatedFeatures=candidate.get('extrapolatedFeatures', []),
                          uncertainty=candidate.get('uncertainty'),
                          referenceAgeSeconds=(generated-reference).total_seconds())
            break
        if result['status'] != 'calculated':
            result['reason'] = 'No complete hydrometric feature window within the three-hour reference-age limit'
    except Exception as exc:
        result['reason'] = f'{type(exc).__name__}: {exc}'
    (out / 'propagation-shadow.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    run_local_nowcast_shadow(out, result)
    return result
