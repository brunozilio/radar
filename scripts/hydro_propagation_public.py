"""Publish the frozen Muçum hydrometric model with its own input contract.

The experimental release is explicitly authorized. Rain coverage and scientific
acceptance thresholds are not operational requirements for this model. Measured
levels, flows, timestamps and immutable provenance remain required.
"""
from datetime import datetime
import math
import re

from hydro_input_readiness import InputsNotReady, MAX_REFERENCE_AGE_HOURS

MODEL_ID = 'radar_mucum_hydrometry_v1'
MODEL_VERSION = 'mucum-hydrometry-public-v1'
SOURCE_MODEL_VERSION = 'mucum-hydrometry-shadow-v1'
MODEL_SHA256 = '8adc838b20fba1ec3edd63db53e4575b0b8df59c22a777ada434ed773fb58c97'
CONTRACT = 'radar-hydrometry-propagation/v1'
SOURCE_FILES = {f'ana-{code}-fresh.xml' for code in ('86510000', '86472000', '86472600', '86500000')} | {
    f'ceran-{plant}-fresh.html' for plant in ('julho', 'monte', 'castro')}


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('Timezone-aware hydrometric timestamp required')
    return result


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Finite hydrometric value required')
    return float(value)


def public_forecast(shadow, *, checked_reference, attempt_id, now, after_reference=None):
    """Convert a freshly computed, complete hydrometric issue into schema 1.

    This creates a new publication document; the original experimental evidence
    remains unchanged in propagation-shadow.json and in immutable archives.
    """
    if (not isinstance(shadow, dict) or shadow.get('schema') != 'radar-propagation-shadow/v1' or
            shadow.get('mode') != 'shadow' or shadow.get('publishable') is not False or
            shadow.get('station') != '86510000'):
        raise ValueError('Invalid hydrometric source document')
    if shadow.get('status') != 'calculated':
        raise InputsNotReady(dict(status='waiting_for_data', modelVersion=MODEL_VERSION,
            rainRequired=False, missing=[shadow.get('reason') or 'Hydrometric measurements are incomplete']))
    if (shadow.get('modelVersion') != SOURCE_MODEL_VERSION or shadow.get('contract') != CONTRACT or
            shadow.get('modelSha256') != MODEL_SHA256 or shadow.get('rainRequired') is not False):
        raise ValueError('Unexpected frozen hydrometric model or input contract')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', attempt_id):
        raise ValueError('Invalid archive attempt identifier')
    if (now.tzinfo is None or checked_reference.tzinfo is None or checked_reference.timestamp() % 3600 or
            timestamp(shadow['checkedReferenceAt']) != checked_reference):
        raise ValueError('Invalid hydrometric polling reference')
    reference = timestamp(shadow['referenceAt'])
    generated = timestamp(shadow['generatedAt'])
    age = (generated-reference).total_seconds()
    if reference.timestamp() % 3600 or reference > checked_reference or generated > now or age < 0:
        raise ValueError('Invalid hydrometric issue chronology')
    if (now-reference).total_seconds() > MAX_REFERENCE_AGE_HOURS * 3600:
        raise InputsNotReady(dict(status='waiting_for_data', modelVersion=MODEL_VERSION, rainRequired=False,
            missing=['Complete hydrometric reference is older than three hours at publication']))
    if after_reference is not None and reference <= after_reference:
        raise InputsNotReady(dict(status='waiting_for_data', modelVersion=MODEL_VERSION, rainRequired=False,
            missing=['No complete hydrometric observation hour newer than the published reference']))
    sources = shadow.get('sources', [])
    if len(sources) != len(SOURCE_FILES) or {source.get('file') for source in sources} != SOURCE_FILES:
        raise ValueError('Missing or duplicate hydrometric source provenance')
    for source in sources:
        if not re.fullmatch(r'[a-f0-9]{64}', source.get('sha256', '')):
            raise ValueError('Missing hydrometric source checksum')
        received = timestamp(source['availableAt'])
        if not 0 <= (generated-received).total_seconds() <= 3600:
            raise ValueError('Hydrometric source was unavailable at issuance')
        if not 0 <= (now-received).total_seconds() <= 3600:
            raise InputsNotReady(dict(status='waiting_for_data', modelVersion=MODEL_VERSION, rainRequired=False,
                missing=['Hydrometric source receipt is stale at publication']))
    observation = shadow.get('observation', {})
    if timestamp(observation['timestamp']) != reference:
        raise ValueError('Hydrometric observation does not match the reference hour')
    observed_level = number(observation['level'])
    points = []
    for source in shadow.get('points', []):
        target = timestamp(source['timestamp'])
        nominal = (target-reference).total_seconds()/3600
        if nominal != source.get('nominalLeadHours') or nominal not in range(1, 7):
            raise ValueError('Invalid nominal hydrometric target')
        if target <= generated:
            raise ValueError('Hydrometric issue contains an expired target')
        point = dict(timestamp=source['timestamp'], level=number(source['level']),
                     nominalLeadHours=int(nominal), realLeadHours=(target-generated).total_seconds()/3600)
        for key in ('lower', 'upper'):
            if key in source:
                point[key] = number(source[key])
        if 'lower' in point and 'upper' in point and point['lower'] > point['upper']:
            raise ValueError('Invalid empirical hydrometric interval')
        if target <= now:
            raise InputsNotReady(dict(status='waiting_for_data', modelVersion=MODEL_VERSION, rainRequired=False,
                missing=['A hydrometric forecast target expired before publication; a fresh issue is required']))
        points.append(point)
    first = int((generated-reference).total_seconds() // 3600) + 1
    if not points or [point['nominalLeadHours'] for point in points] != list(range(first, 7)):
        raise ValueError('Expected the strictly future suffix of hydrometric H+1 through H+6 targets')
    return dict(schema=1, station='mucum', generatedAt=shadow['generatedAt'],
        referenceAt=shadow['referenceAt'], experimental=True, intervalMinutes=15,
        modelVersion=MODEL_VERSION, sourceModelVersion=SOURCE_MODEL_VERSION, modelSha256=MODEL_SHA256,
        featureContract=CONTRACT, rainRequired=False, horizonHours=6,
        forecastStartLeadHours=points[0]['nominalLeadHours'], referenceAgeSeconds=age,
        checkedReferenceAt=checked_reference.isoformat(),
        archiveReceiptKey=f'projection/receipts/{attempt_id}.json',
        observation=dict(timestamp=observation['timestamp'], level=observed_level),
        models=[dict(id=MODEL_ID, label='Modelo hidrométrico', points=points)],
        extrapolatedFeatures=shadow.get('extrapolatedFeatures', []), uncertainty=shadow.get('uncertainty'),
        accuracy=dict(goalPercent=98, demonstrated=False, status='experimental'))
