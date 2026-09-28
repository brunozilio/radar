"""Pure, causal short-term shadow candidate; never publishes or fits a model.

The public forecast remains the caller's unchanged baseline. This module only
returns a separate audit artifact. See docs/radar-short-term-shadow-protocol.json.
"""
import hashlib
import json
import math
from datetime import datetime


VERSION = 'radar-short-term-shadow-v1'
STATION = '86510000'
MAX_CORRECTION_M = 0.5
FORMULA = {
    'maximumWeight': 0.5,
    'fullWeightUntilRealHours': 1.0,
    'zeroWeightAtRealHours': 3.0,
    'maximumAbsoluteCorrectionM': MAX_CORRECTION_M,
    'trendLookbackHours': 1.0,
    'directionThresholdMPerHour': 0.05,
}


def _safe(value):
    """Keep rejected inputs JSON serializable without hiding their invalidity."""
    if isinstance(value, float) and not math.isfinite(value):
        return {'invalidNumber': str(value)}
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _hash(value):
    return hashlib.sha256(json.dumps(_safe(value), sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _time(value):
    if not isinstance(value, str):
        raise ValueError('Timestamp must be an ISO string')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('Timezone is required')
    return result


def _level(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Level must be numeric')
    if not math.isfinite(value) or value < 0:
        raise ValueError('Level must be finite and nonnegative')
    return float(value)


def _observation(row, expected_time, issued, station, allow_legacy):
    if not isinstance(row, dict) or row.get('station') != station:
        raise ValueError('Observation station mismatch')
    if _time(row.get('timestamp')) != expected_time:
        raise ValueError('Exact required observation timestamp is missing')
    received = _time(row.get('received_at'))
    if received > issued or received < expected_time:
        raise ValueError('Observation was not received between observation and issue time')
    quality = row.get('quality')
    if quality != 'approved' and not (allow_legacy and quality == 'legacy_unverified'):
        raise ValueError('Approved observation quality is required')
    if not isinstance(row.get('evidence_id'), str) or not row['evidence_id'].strip():
        raise ValueError('Observation evidence identifier is missing')
    return _level(row.get('level'))


def blend_weight(real_lead_h):
    if not math.isfinite(real_lead_h) or real_lead_h <= 0:
        raise ValueError('Real lead must be positive and finite')
    if real_lead_h <= 1:
        return 0.5
    return max(0.0, 0.25 * (3.0 - real_lead_h))


def build_shadow(*, reference_at, issued_at, anchor, received_history,
                 baseline_points, station=STATION, allow_legacy_unverified=False):
    """Return shadow evidence; expected missing/invalid inputs fail closed.

    Observations contain station, timestamp, level, received_at, quality and
    evidence_id. Point keys are timestamp and level. Neither actual target
    observations nor fitted parameters are accepted by this interface.
    """
    # Materialize once so iterators cannot be consumed differently by validation
    # and provenance hashing. No caller object is modified.
    history = list(received_history)
    baseline = list(baseline_points)
    inputs = dict(reference_at=reference_at, issued_at=issued_at, station=station,
        anchor=anchor, received_history=history, baseline_points=baseline,
        allow_legacy_unverified=allow_legacy_unverified)
    report = {
        'schema': 1, 'candidateVersion': VERSION, 'mode': 'shadow',
        'publishable': False, 'promoted': False, 'goalEvidenceEligible': False,
        'referenceAt': reference_at, 'issuedAt': issued_at, 'station': station,
        'formula': dict(FORMULA), 'inputSha256': _hash(inputs),
        'inputEvidence': _safe(inputs), 'status': 'unavailable',
        'reasons': [], 'points': [],
    }
    try:
        if station != STATION:
            raise ValueError('Candidate is registered only for Muçum')
        reference, issued = _time(reference_at), _time(issued_at)
        if reference.minute or reference.second or reference.microsecond:
            raise ValueError('Reference must be an exact hour')
        if not 0 <= (issued - reference).total_seconds() < 3600:
            raise ValueError('Issue must be within its reference hour')
        anchor_level = _observation(anchor, reference, issued, station,
                                    allow_legacy_unverified)
        needed_epoch = reference.timestamp() - 3600
        matches = []
        for row in history:
            if row.get('station') != station:
                continue
            # Malformed unrelated rows cannot become a substitute for the exact
            # timestamp. At the required timestamp every revision must be valid.
            try:
                observation_time = _time(row.get('timestamp'))
            except (ValueError, TypeError):
                continue
            if observation_time.timestamp() == needed_epoch:
                matches.append(row)
        if not matches:
            raise ValueError('Exact level at anchor minus one hour is unavailable')
        past_values = [_observation(row, _time(row['timestamp']), issued,
                                   station, allow_legacy_unverified) for row in matches]
        if len(set(past_values)) != 1:
            raise ValueError('Conflicting revisions at the required past timestamp')
        slope = anchor_level - past_values[0]
        points, targets = [], set()
        for point in baseline:
            target = _time(point.get('timestamp'))
            target_epoch = target.timestamp()
            if target_epoch in targets:
                raise ValueError('Duplicate baseline target')
            targets.add(target_epoch)
            base = _level(point.get('level'))
            lead = (target - issued).total_seconds() / 3600
            weight = blend_weight(lead)
            trend = anchor_level + slope * (target - reference).total_seconds() / 3600
            raw_correction = weight * (trend - base)
            correction = max(-MAX_CORRECTION_M, min(MAX_CORRECTION_M, raw_correction))
            candidate = base + correction
            if not math.isfinite(candidate) or candidate < 0:
                raise ValueError('Candidate level is invalid')
            points.append({
                'timestamp': point['timestamp'], 'realLeadHours': lead,
                'baselineLevel': base, 'shadowLevel': candidate,
                'linearTrendLevel': trend, 'weight': weight,
                'correctionM': correction, 'correctionWasCapped': correction != raw_correction,
                'status': 'shadow_corrected' if weight else 'unchanged_long_lead',
            })
        if not points:
            raise ValueError('Baseline has no points')
        used = [anchor, *matches]
        legacy = any(row['quality'] == 'legacy_unverified' for row in used)
        report.update(status='shadow_generated', points=points, slopeMPerHour=slope,
            directionKnownAtIssue='rising' if slope > 0.05 else 'falling' if slope < -0.05 else 'stable',
            receiptEvidence='legacy_created_at_unverified' if legacy else 'approved_received_observations',
            usedObservationEvidenceIds=[row['evidence_id'] for row in used],
            reasons=['Legacy D1 created_at cannot establish immutable historical versions or QC'] if legacy else [])
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        report['reasons'] = [str(exc)]
    return report
