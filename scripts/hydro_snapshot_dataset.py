"""Build an offline causal dataset from saved feature receipts and exact labels.

No network, fitting, model loading, promotion, or changes to frozen inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from hydro_feature_contract import (
    ContractError, FEATURE_CONTRACT_ID, canonical_sha256, feature_names,
    select_exact_observation, timestamp, validate_snapshot,
)

SPLITS = ('train', 'validation', 'test')


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def check_plan(plan):
    """Require declared chronology, whole-event assignment and sample thresholds."""
    cutoffs = [timestamp(plan[key]) for key in ('train_end', 'validation_end', 'test_end')]
    if not cutoffs[0] < cutoffs[1] < cutoffs[2]:
        raise ContractError('Expected train_end < validation_end < test_end')
    timestamp(plan['as_of'])
    horizons = plan.get('nominal_horizons_hours')
    if (not isinstance(horizons, list) or not horizons or
            any(type(h) is not int or not 1 <= h <= 12 for h in horizons) or
            len(set(horizons)) != len(horizons)):
        raise ContractError('Declare unique nominal horizons of 1..12 hours')
    embargo = plan.get('embargo_hours', 0)
    if isinstance(embargo, bool) or not isinstance(embargo, (int, float)) or not 0 <= embargo <= 720:
        raise ContractError('Embargo must be between zero and 720 hours')
    for name in ('minimum_rows_per_horizon', 'minimum_events_per_split'):
        requirements = plan.get(name)
        if (not isinstance(requirements, dict) or set(requirements) != set(SPLITS) or
                any(type(requirements[s]) is not int or requirements[s] < 1 for s in SPLITS)):
            raise ContractError(f'Declare positive train/validation/test thresholds in {name}')
    intervals = []
    identities = set()
    if not isinstance(plan.get('events'), list) or not plan['events']:
        raise ContractError('Whole-event holdout definitions required')
    boundaries = dict(zip(SPLITS, ((float('-inf'), cutoffs[0]), (cutoffs[0], cutoffs[1]), (cutoffs[1], cutoffs[2]))))
    for event in plan['events']:
        identity, split = event.get('id'), event.get('split')
        if not isinstance(identity, str) or not identity or identity in identities:
            raise ContractError('Event IDs must be nonempty and unique')
        identities.add(identity)
        if split not in SPLITS:
            raise ContractError(f'{identity}: unknown split')
        start, end = timestamp(event.get('start_at')), timestamp(event.get('end_at'))
        left, right = boundaries[split]
        if not left <= start < end <= right:
            raise ContractError(f'{identity}: event crosses its chronological split')
        intervals.append(dict(id=identity, split=split, start=start, end=end))
    ordered = sorted(intervals, key=lambda event: event['start'])
    if any(left['end'] > right['start'] for left, right in zip(ordered, ordered[1:])):
        raise ContractError('Events overlap; a physical origin cannot belong to two holdouts')
    return intervals, dict(zip(SPLITS, cutoffs))


def build_dataset(snapshots, observations, plan):
    events, cutoffs = check_plan(plan)
    as_of = timestamp(plan['as_of'])
    embargo = plan.get('embargo_hours', 0) * 3600
    rejections, candidates = [], defaultdict(list)
    seen = set()

    def reject(reason, snapshot_index=None, **details):
        rejections.append(dict(reason=reason, snapshot_index=snapshot_index, **details))

    for index, snapshot in enumerate(snapshots):
        errors = validate_snapshot(snapshot)
        if errors:
            reject('invalid_feature_contract', index, details=errors)
            continue
        if snapshot['contract_id'] != FEATURE_CONTRACT_ID:
            reject('unsupported_training_contract', index, contract_id=snapshot['contract_id'])
            continue
        digest = canonical_sha256(snapshot)
        if digest in seen:
            reject('duplicate_snapshot', index, snapshot_sha256=digest)
            continue
        seen.add(digest)
        if timestamp(snapshot['issued_at']) > as_of:
            reject('snapshot_not_yet_available', index)
            continue
        key = snapshot['station_id'], snapshot['datum_id'], timestamp(snapshot['reference_at'])
        candidates[key].append((index, snapshot, digest))
    selected = []
    for group in candidates.values():
        instants = Counter(timestamp(snapshot['issued_at']) for _, snapshot, _ in group)
        if any(count > 1 for count in instants.values()):
            for index, _, _ in group:
                reject('conflicting_snapshots_at_same_issuance', index)
            continue
        group.sort(key=lambda entry: timestamp(entry[1]['issued_at']))
        selected.append(group[-1])
        for index, _, digest in group[:-1]:
            reject('superseded_same_reference', index, snapshot_sha256=digest)
    rows = []
    for index, snapshot, digest in sorted(selected, key=lambda entry: timestamp(entry[1]['issued_at'])):
        reference, issued = timestamp(snapshot['reference_at']), timestamp(snapshot['issued_at'])
        member = [event for event in events if event['start'] <= reference < event['end']]
        if not member:
            reject('origin_outside_declared_events', index)
            continue
        event = member[0]
        split = event['split']
        for horizon in plan['nominal_horizons_hours']:
            target = reference + horizon * 3600
            details = dict(nominal_lead_h=horizon, event_id=event['id'], split=split,
                           target_at=iso(target), snapshot_sha256=digest)
            # This purges training labels at the next split and targets crossing
            # an event boundary. There is no random row split or event reuse.
            if target + embargo >= min(event['end'], cutoffs[split]):
                reject('purged_target_crosses_event_or_split', index, **details)
                continue
            if target <= issued:
                reject('target_elapsed_at_issuance', index, **details)
                continue
            if target > as_of:
                reject('target_not_yet_observed', index, **details)
                continue
            known = min(as_of, cutoffs['train'] - .000001) if split == 'train' else as_of
            try:
                label = select_exact_observation(observations, station_id=snapshot['station_id'],
                                                 datum_id=snapshot['datum_id'], valid_at=iso(target), known_at=iso(known))
            except (ContractError, TypeError, ValueError) as exc:
                reject('exact_label_unavailable', index, details=str(exc), **details)
                continue
            rows.append(dict(split=split, event_id=event['id'], contract_id=snapshot['contract_id'], station_id=snapshot['station_id'],
                             datum_id=snapshot['datum_id'], reference_at=snapshot['reference_at'],
                             issued_at=snapshot['issued_at'], target_at=iso(target),
                             nominal_lead_h=horizon, actual_lead_h=(target - issued) / 3600,
                             snapshot_sha256=digest, features=snapshot['features'],
                             anchor_m=snapshot['features'][0], observed_m=label['level_m'],
                             delta_m=label['level_m'] - snapshot['features'][0],
                             label_available_at=label['available_at'],
                             label_receipt_sha256=label.get('receipt_sha256'),
                             label_source=label.get('source')))
    counts, insufficient = [], []
    for split in SPLITS:
        for horizon in plan['nominal_horizons_hours']:
            group = [row for row in rows if row['split'] == split and row['nominal_lead_h'] == horizon]
            event_ids = sorted({row['event_id'] for row in group})
            counts.append(dict(split=split, nominal_lead_h=horizon, rows=len(group), events=event_ids))
            if len(group) < plan['minimum_rows_per_horizon'][split]:
                insufficient.append(f'{split}/{horizon}h: {len(group)} rows below required {plan["minimum_rows_per_horizon"][split]}')
            if len(event_ids) < plan['minimum_events_per_split'][split]:
                insufficient.append(f'{split}/{horizon}h: {len(event_ids)} events below required {plan["minimum_events_per_split"][split]}')
    return dict(schema='radar-causal-dataset/v1', contract_id=FEATURE_CONTRACT_ID,
                feature_names=feature_names(), plan=plan, rows=rows, rejections=rejections,
                summary=dict(input_snapshots=len(snapshots), selected_snapshots=len(selected), rows=len(rows),
                             availability=counts, rejection_counts=dict(Counter(r['reason'] for r in rejections)),
                             insufficient_data=insufficient, experiment_ready=not insufficient,
                             validation_status='not_evaluated', promotion_allowed=False, accuracy_claim_allowed=False),
                limitations=['Saved input vectors and declared receipts are preserved, not recomputed or independently certified from raw data here.',
                             'Whole-event definitions must be fixed externally; names alone do not certify independent floods.',
                             'Readiness for an offline experiment does not establish model accuracy, validation success, or permission to promote.',
                             'Nominal horizons differ from elapsed-time lead; retain both in all evaluations.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots', nargs='+', type=Path, required=True)
    parser.add_argument('--observations', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = [*args.snapshots, args.observations, args.plan]
    manifest = [dict(path=str(path.resolve()), sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
    snapshots = []
    for path in args.snapshots:
        payload = json.loads(path.read_text())
        snapshots.extend(payload if isinstance(payload, list) else [payload])
    result = build_dataset(snapshots, json.loads(args.observations.read_text()), json.loads(args.plan.read_text()))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'dataset.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    (args.output / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    return 0 if result['summary']['experiment_ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
