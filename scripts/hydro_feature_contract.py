"""Causal feature receipts for future Radar models; no fitting or legacy conversion.

The contract describes the exact vector observed at issuance. It does not certify
that an older model was trained with this contract or that its accuracy is known.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from numbers import Real

FEATURE_CONTRACT_ID = 'radar-180-contemporaneous/v2'
LEGACY_FEATURE_CONTRACT_ID = 'radar-180-contemporaneous/v1'
MAX_REFERENCE_AGE_SECONDS = 3 * 3600
TARGET_POLICY = 'Only original H+1..H+6 targets strictly future at actual issuance'
SNAPSHOT_SCHEMA = 'radar-feature-snapshot/v1'
LEVELS = ('86510000', '86472000', '86472600', '86500000')
PLANTS = ('julho', 'monte', 'castro')
GROUPS = ('Baixo Antas', 'Carreiro', 'Prata-Turvo', 'Alto Antas', 'Tainhas')
NWP_MODELS = ('gfs_seamless', 'ecmwf_ifs025', 'icon_global')
NWP_WINDOWS = (3, 6, 9, 12)
SHA256 = re.compile(r'^[0-9a-f]{64}$')


class ContractError(ValueError):
    pass


def timestamp(value):
    """Reject timezone assumptions: receipts must supply an explicit offset."""
    if not isinstance(value, str):
        raise ContractError('Timestamp must be an ISO string with an explicit timezone')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ContractError(f'Invalid timestamp: {value}') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f'Timezone missing: {value}')
    return parsed.timestamp()


def finite(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def canonical_sha256(value):
    body = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode()
    return hashlib.sha256(body).hexdigest()


def feature_definitions():
    fields = []
    def add(name, unit, transformation, minimum=None, maximum=None):
        fields.append(dict(name=name, unit=unit, transformation=transformation,
                           minimum=minimum, maximum=maximum))
    for station in LEVELS:
        add(f'{station}:H', 'm', 'Approved exact reference-hour level', 0)
        for hours in (.5, 1, 2, 4, 8):
            add(f'{station}:dH{hours}', 'm/h',
                f'(H(reference)-H_asof(reference-{hours}h))/{hours}; historical asof age<=900s, current hour exact')
    for plant in PLANTS:
        add(f'{plant}:Q06', '(1000 m3/s)^0.6', '(outflow_m3_s/1000)^0.6', 0)
        add(f'{plant}:Q', '1000 m3/s', 'outflow_m3_s/1000', 0)
        add(f'{plant}:I', '1000 m3/s', 'inflow_m3_s/1000', 0)
        for hours in (1, 2, 4, 8):
            add(f'{plant}:dQ{hours}', '(1000 m3/s)^0.6/h',
                f'(Q06(reference)-Q06_asof(reference-{hours}h))/{hours}; historical asof age<=5400s, current hour exact')
    for group in GROUPS:
        for hours in (1, 3, 6, 12, 24, 48):
            add(f'{group}:P{hours}', 'mm',
                f'Fixed spatial weights in (reference-{hours}h,reference]; measured intervals<=5400s, partial interval proportional allocation; missing gauges add zero amount and coverage; no renormalization; coverage>=0.5', 0)
            add(f'{group}:C{hours}', 'fraction',
                'Fixed spatially weighted measured temporal coverage; no extension after interval end', .5, 1)
        for lag in (3, 6, 12):
            add(f'{group}:P3lag{lag}', 'mm', f'Measured 3h rain ending at reference-{lag}h', 0)
    for model in NWP_MODELS:
        for group in GROUPS:
            for hours in NWP_WINDOWS:
                add(f'nwp:{model}:{group}:P{hours}', 'mm',
                    f'Sum current_forecast precipitation at exact reference+1h..+{hours}h; received before issuance', 0)
    assert len(fields) == 180
    return fields


def feature_names():
    return [field['name'] for field in feature_definitions()]


def contract_specification():
    return dict(id=FEATURE_CONTRACT_ID, features=feature_definitions(),
                feature_count=180, observed_feature_count=120,
                rain_regions=list(GROUPS), nwp_location_order=list(GROUPS),
                observed_time_policy='Exact reference hour; no source delay applied to the feature clock',
                reference_age_policy='0 <= actual issuance minus reference <= 10800 seconds; preserve the original reference and target clock',
                max_reference_age_seconds=MAX_REFERENCE_AGE_SECONDS,
                availability_policy='Every input receipt must precede or equal actual issuance and be no more than 3600 seconds old at issuance',
                nwp_product='current_forecast', nwp_field='precipitation',
                missing_policy='Reject missing/nonfinite final features; never impute the final vector or substitute historical NWP. Historical lag asof and partial rain-interval allocation are explicit in each transformation.',
                target_policy=TARGET_POLICY,
                target_identity_policy='Exact same station/datum; nominal and actual lead retained separately',
                status='Data contract only; no model validation or promotion')


def require_training_contract(contract_id):
    """A caller must declare its training data contract; legacy absence is an error."""
    if contract_id != FEATURE_CONTRACT_ID:
        raise ContractError('Training blocked: contemporaneous feature receipts required; '
                            'precipitation_previous_day1 is not equivalent to current precipitation')


def current_nwp_features(forecasts, reference_at):
    """Exact current-product windows, sharing the contract's 60-column order.

    Availability is checked on receipts by validate_snapshot. This function never
    substitutes previous-day, observed, reanalysis, or missing precipitation.
    """
    reference = timestamp(reference_at)
    values = []
    for model in NWP_MODELS:
        locations = forecasts.get(model)
        if not isinstance(locations, list) or len(locations) != len(GROUPS):
            raise ContractError(f'{model}: expected five ordered current-forecast locations')
        for location in locations:
            hourly = location.get('hourly', {})
            if any('previous_day' in name for name in hourly):
                raise ContractError(f'{model}: historical previous-day NWP is forbidden')
            if location.get('hourly_units', {}).get('precipitation') != 'mm':
                raise ContractError(f'{model}: current precipitation unit must be mm')
            offset = location.get('utc_offset_seconds')
            if not isinstance(offset, int) or isinstance(offset, bool) or abs(offset) >= 86400:
                raise ContractError(f'{model}: explicit forecast UTC offset required')
            times, rain = hourly.get('time'), hourly.get('precipitation')
            if not isinstance(times, list) or not isinstance(rain, list) or len(times) != len(rain):
                raise ContractError(f'{model}: malformed current precipitation series')
            lookup = {}
            for valid_at, amount in zip(times, rain):
                try:
                    parsed = datetime.fromisoformat(valid_at.replace('Z', '+00:00'))
                except (AttributeError, TypeError, ValueError) as exc:
                    raise ContractError(f'{model}: invalid NWP valid time') from exc
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone(timedelta(seconds=offset)))
                instant = parsed.timestamp()
                if instant in lookup:
                    raise ContractError(f'{model}: duplicate NWP valid time')
                lookup[instant] = amount
            for hours in NWP_WINDOWS:
                window = [lookup.get(reference + hour * 3600) for hour in range(1, hours + 1)]
                if not all(finite(value) and value >= 0 for value in window):
                    raise ContractError(f'{model}: missing/invalid exact current precipitation window {hours}h')
                values.append(float(sum(window)))
    return values


def validate_snapshot(snapshot):
    """Return all usable diagnostics; malformed receipts fail closed."""
    errors = []
    if not isinstance(snapshot, dict):
        return ['Snapshot must be an object']
    if snapshot.get('schema') != SNAPSHOT_SCHEMA:
        errors.append('Unknown snapshot schema')
    contract_id = snapshot.get('contract_id')
    if contract_id not in (FEATURE_CONTRACT_ID, LEGACY_FEATURE_CONTRACT_ID):
        errors.append('Wrong feature contract; legacy predictors cannot be relabeled')
    for key in ('station_id', 'datum_id'):
        if not isinstance(snapshot.get(key), str) or not snapshot[key].strip():
            errors.append(f'Missing {key}')
    if snapshot.get('station_id') != LEVELS[0]:
        errors.append('This 180-feature contract belongs only to Muçum 86510000')
    reference = issued = None
    for key in ('reference_at', 'issued_at'):
        try:
            value = timestamp(snapshot.get(key))
            if key == 'reference_at':
                reference = value
            else:
                issued = value
        except ContractError as exc:
            errors.append(f'{key}: {exc}')
    if reference is not None and reference % 3600:
        errors.append('Reference must be an exact hour')
    if reference is not None and issued is not None:
        age = issued - reference
        if contract_id == LEGACY_FEATURE_CONTRACT_ID:
            # Historical receipts keep their original contract and semantics.
            if not 0 <= age < 3600:
                errors.append('Issuance must occur in its reference hour, before every nominal target')
        elif contract_id == FEATURE_CONTRACT_ID:
            if not 0 <= age <= MAX_REFERENCE_AGE_SECONDS:
                errors.append('Reference age at issuance must be between 0 and 10800 seconds')
            recorded_age = snapshot.get('reference_age_seconds')
            if not finite(recorded_age) or not math.isclose(recorded_age, age, rel_tol=0, abs_tol=1e-6):
                errors.append('reference_age_seconds must match actual issuance minus reference')
    if contract_id == FEATURE_CONTRACT_ID and snapshot.get('target_policy') != TARGET_POLICY:
        errors.append('Original reference-hour targets must remain strictly future at actual issuance')
    if snapshot.get('feature_names') != feature_names():
        errors.append('Feature names/order do not match the 180-column contract')
    values = snapshot.get('features')
    vector_ok = isinstance(values, list) and len(values) == 180
    if not vector_ok:
        errors.append('Expected exactly 180 feature values')
    else:
        for index, (value, definition) in enumerate(zip(values, feature_definitions())):
            if not finite(value):
                errors.append(f'Feature {index} {definition["name"]}: missing/non-finite value')
            elif ((definition['minimum'] is not None and value < definition['minimum'] - 1e-9) or
                  (definition['maximum'] is not None and value > definition['maximum'] + 1e-9)):
                errors.append(f'Feature {index} {definition["name"]}: outside physical/coverage bounds')
    readiness = snapshot.get('input_readiness')
    if not isinstance(readiness, dict) or readiness.get('status') != 'ready':
        errors.append('Complete same-hour input readiness required')
    else:
        try:
            if timestamp(readiness.get('referenceAt')) != reference:
                errors.append('Readiness reference does not match feature reference')
        except ContractError as exc:
            errors.append(f'Readiness timestamp: {exc}')
        groups = {}
        for name in ('levels', 'flows', 'rainCoverage'):
            groups[name] = readiness.get(name)
            if not isinstance(groups[name], dict):
                errors.append(f'Readiness {name} must be an object')
                groups[name] = {}
        for index, station in enumerate(LEVELS):
            level = groups['levels'].get(station)
            if not finite(level) or level < 0:
                errors.append(f'{station}: exact approved level missing')
            elif vector_ok and finite(values[index * 6]) and not math.isclose(values[index * 6], level, abs_tol=1e-9):
                errors.append(f'{station}: feature anchor differs from ready observation')
        for index, plant in enumerate(PLANTS):
            flow = groups['flows'].get(plant)
            if not isinstance(flow, list) or len(flow) != 2 or not all(finite(v) and v >= 0 for v in flow):
                errors.append(f'{plant}: exact outflow/inflow missing')
            elif vector_ok:
                transformed = ((flow[0] / 1000) ** .6, flow[0] / 1000, flow[1] / 1000)
                for offset, value in enumerate(transformed):
                    feature = values[24 + index * 7 + offset]
                    if finite(feature) and not math.isclose(feature, value, rel_tol=1e-9, abs_tol=1e-9):
                        errors.append(f'{plant}: flow feature differs from ready observation')
        for group in GROUPS:
            cover = groups['rainCoverage'].get(group)
            if not finite(cover) or not .5 - 1e-9 <= cover <= 1 + 1e-9:
                errors.append(f'{group}: complete-hour measured coverage below 50% or invalid')
    sources = snapshot.get('sources')
    found = set()
    if not isinstance(sources, list):
        errors.append('Input source receipts required')
    else:
        for source in sources:
            if not isinstance(source, dict):
                errors.append('Invalid source receipt')
                continue
            identity = source.get('kind'), source.get('id')
            if not all(isinstance(v, str) for v in identity):
                errors.append('Source kind/id missing')
                continue
            if identity in found:
                errors.append(f'{identity}: duplicate source receipt')
            found.add(identity)
            if not SHA256.fullmatch(str(source.get('sha256', ''))):
                errors.append(f'{identity}: source SHA256 missing/invalid')
            try:
                available = timestamp(source.get('available_at'))
                if issued is not None and available > issued:
                    errors.append(f'{identity}: received after issuance')
                freshness_clock = issued if contract_id == FEATURE_CONTRACT_ID else reference
                if freshness_clock is not None and available < freshness_clock - 3600:
                    errors.append(f'{identity}: current input receipt is stale')
                if identity[0] == 'observed':
                    through = source.get('observed_through')
                    if identity[1] in (*LEVELS, *PLANTS) and timestamp(through) != reference:
                        errors.append(f'{identity}: current observation must match exact reference hour')
                    if through is not None and (timestamp(through) > available or
                                                (reference is not None and timestamp(through) > reference)):
                        errors.append(f'{identity}: observed data beyond its causal cutoff')
                elif identity[0] == 'nwp':
                    if source.get('product') != 'current_forecast' or source.get('field') != 'precipitation':
                        errors.append(f'{identity}: only current_forecast precipitation is admissible; no previous_day1')
                    nwp_reference = source.get('forecast_reference_at')
                    if nwp_reference is not None and timestamp(nwp_reference) > available:
                        errors.append(f'{identity}: NWP issuance after receipt')
                else:
                    errors.append(f'{identity}: unsupported source kind')
            except ContractError as exc:
                errors.append(f'{identity}: {exc}')
    for identity in [('observed', v) for v in (*LEVELS, *PLANTS)] + [('nwp', v) for v in NWP_MODELS]:
        if identity not in found:
            errors.append(f'{identity}: required source receipt missing')
    if not isinstance(snapshot.get('model'), dict):
        errors.append('Model/runtime provenance required; this does not certify legacy compatibility')
    return errors


def build_snapshot(*, reference_at, issued_at, station_id, datum_id, feature_values,
                   sources, input_readiness, model_metadata):
    original = list(feature_values)
    # A null must stay missing and be rejected, rather than becoming zero.
    values = [float(v) if finite(v) else v for v in original]
    snapshot = dict(schema=SNAPSHOT_SCHEMA, contract_id=FEATURE_CONTRACT_ID,
                    station_id=station_id, datum_id=datum_id,
                    reference_at=reference_at, issued_at=issued_at,
                    reference_age_seconds=timestamp(issued_at) - timestamp(reference_at),
                    target_policy=TARGET_POLICY,
                    feature_names=feature_names(), features=values,
                    sources=sources, input_readiness=input_readiness, model=model_metadata)
    errors = validate_snapshot(snapshot)
    if errors:
        raise ContractError('; '.join(errors))
    # Round-trip also rejects metadata NaNs and detaches mutable caller objects.
    try:
        return json.loads(json.dumps(snapshot, allow_nan=False, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise ContractError('Snapshot metadata must be finite and JSON serializable') from exc


def select_exact_observation(records, *, station_id, datum_id, valid_at, known_at):
    """Latest received version of one exact observation; never fall back to old QC."""
    valid, known = timestamp(valid_at), timestamp(known_at)
    matches = []
    for row in records:
        if row.get('station_id') != station_id or row.get('datum_id') != datum_id:
            continue
        if timestamp(row.get('valid_at')) != valid:
            continue
        available = timestamp(row.get('available_at'))
        if available <= known:
            matches.append((available, row))
    if not matches:
        raise ContractError('Exact same-station/datum observation unavailable by cutoff')
    latest = max(available for available, _ in matches)
    selected = [row for available, row in matches if available == latest]
    if len({(row.get('level_m'), row.get('quality')) for row in selected}) != 1:
        raise ContractError('Conflicting observation revisions at identical availability')
    row = selected[0]
    if row.get('quality') != 'approved' or not finite(row.get('level_m')) or row['level_m'] < 0:
        raise ContractError('Latest exact observation is missing, invalid, or unapproved')
    if not SHA256.fullmatch(str(row.get('receipt_sha256', ''))):
        raise ContractError('Exact observation receipt SHA256 missing/invalid')
    if valid > latest:
        raise ContractError('Observed timestamp is after its receipt')
    return row
