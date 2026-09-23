import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from hydro_feature_contract import (
    ContractError, FEATURE_CONTRACT_ID, LEGACY_FEATURE_CONTRACT_ID,
    MAX_REFERENCE_AGE_SECONDS, TARGET_POLICY, GROUPS, LEVELS, NWP_MODELS, PLANTS,
    build_snapshot, contract_specification, current_nwp_features, feature_names,
    require_training_contract, select_exact_observation, validate_snapshot,
)
from hydro_snapshot_dataset import build_dataset


def sample_snapshot(reference='2026-01-01T12:00:00-03:00', *,
                    issued_delay_seconds=1200, receipt_age_seconds=600):
    ref = datetime.fromisoformat(reference)
    issued_time = ref + timedelta(seconds=issued_delay_seconds)
    received = (issued_time - timedelta(seconds=receipt_age_seconds)).isoformat()
    issued = issued_time.isoformat()
    vector = [0.] * 180
    for i in range(4):
        vector[i * 6] = 10.
    for i in range(3):
        vector[24 + i * 7:27 + i * 7] = [1., 1., 1.]
    for i in range(5):
        for j in range(6):
            vector[45 + i * 15 + j * 2 + 1] = 1.
    sources = [dict(kind='observed', id=source, available_at=received,
                    observed_through=reference, sha256='a' * 64) for source in (*LEVELS, *PLANTS)]
    sources += [dict(kind='nwp', id=model, available_at=received, sha256='b' * 64,
                     product='current_forecast', field='precipitation', forecast_reference_at=None) for model in NWP_MODELS]
    readiness = dict(status='ready', referenceAt=reference, levels={s: 10. for s in LEVELS},
                     flows={p: [1000., 1000.] for p in PLANTS}, rainCoverage={g: 1. for g in GROUPS})
    return build_snapshot(reference_at=reference, issued_at=issued, station_id=LEVELS[0],
                          datum_id='ANA:86510000:reference-v1', feature_values=vector,
                          sources=sources, input_readiness=readiness,
                          model_metadata={'id': 'fixture', 'training_contract_id': 'legacy-unverified', 'runtime': {'python': 'fixture'}})


def sample_label(snapshot, lead=1):
    target = datetime.fromisoformat(snapshot['reference_at']) + timedelta(hours=lead)
    return dict(station_id=snapshot['station_id'], datum_id=snapshot['datum_id'],
                valid_at=target.isoformat(), available_at=(target + timedelta(minutes=5)).isoformat(),
                level_m=10.25, quality='approved', source='ANA/SNIRH', receipt_sha256='c' * 64)


def sample_plan():
    return dict(train_end='2026-01-03T00:00:00-03:00', validation_end='2026-01-05T00:00:00-03:00',
                test_end='2026-01-07T00:00:00-03:00', as_of='2026-01-07T00:00:00-03:00',
                nominal_horizons_hours=[1], embargo_hours=0,
                minimum_rows_per_horizon=dict(train=1, validation=1, test=1),
                minimum_events_per_split=dict(train=1, validation=1, test=1),
                events=[dict(id=split + '-event', split=split,
                             start_at=f'2026-01-{start:02}T00:00:00-03:00',
                             end_at=f'2026-01-{end:02}T00:00:00-03:00')
                        for split, start, end in [('train', 1, 3), ('validation', 3, 5), ('test', 5, 7)]])


class FeatureContractTests(unittest.TestCase):
    def test_exact_order_units_and_count(self):
        names = feature_names()
        self.assertEqual(len(names), 180)
        self.assertEqual(len(set(names)), 180)
        self.assertEqual(names[:6], ['86510000:H', '86510000:dH0.5', '86510000:dH1', '86510000:dH2', '86510000:dH4', '86510000:dH8'])
        self.assertEqual(names[24], 'julho:Q06')
        self.assertEqual(names[45], 'Baixo Antas:P1')
        self.assertEqual(names[119], 'Tainhas:P3lag12')
        self.assertEqual(names[120], 'nwp:gfs_seamless:Baixo Antas:P3')
        self.assertEqual(names[-1], 'nwp:icon_global:Tainhas:P12')
        self.assertIn('asof age<=900s', contract_specification()['features'][1]['transformation'])

    def test_snapshot_can_describe_legacy_model_without_certifying_its_training(self):
        snapshot = sample_snapshot()
        self.assertEqual(validate_snapshot(snapshot), [])
        self.assertEqual(snapshot['model']['training_contract_id'], 'legacy-unverified')
        for legacy in [None, '', 'previous_day1', 'legacy-unverified', LEGACY_FEATURE_CONTRACT_ID]:
            with self.assertRaises(ContractError):
                require_training_contract(legacy)
        require_training_contract(FEATURE_CONTRACT_ID)

    def test_v2_describes_age_and_preserves_original_reference_and_feature_clock(self):
        immediate = sample_snapshot()
        delayed = sample_snapshot(issued_delay_seconds=MAX_REFERENCE_AGE_SECONDS)
        self.assertEqual(delayed['contract_id'], 'radar-180-contemporaneous/v2')
        self.assertEqual(delayed['reference_age_seconds'], 10800)
        self.assertEqual(delayed['target_policy'], TARGET_POLICY)
        self.assertEqual(delayed['reference_at'], immediate['reference_at'])
        self.assertEqual(delayed['input_readiness'], immediate['input_readiness'])
        self.assertEqual(delayed['feature_names'], immediate['feature_names'])
        self.assertEqual(delayed['features'], immediate['features'])
        self.assertEqual(validate_snapshot(delayed), [])
        specification = contract_specification()
        self.assertEqual(specification['max_reference_age_seconds'], 10800)
        self.assertEqual(specification['target_policy'], TARGET_POLICY)

    def test_reference_age_zero_and_three_hours_inclusive(self):
        for delay in (0, 3600, 10800):
            with self.subTest(delay=delay):
                self.assertEqual(validate_snapshot(sample_snapshot(
                    issued_delay_seconds=delay, receipt_age_seconds=0)), [])
        for delay in (-.000001, 10800.000001):
            with self.subTest(delay=delay), self.assertRaisesRegex(ContractError, 'between 0 and 10800'):
                sample_snapshot(issued_delay_seconds=delay, receipt_age_seconds=0)

    def test_v2_recorded_age_and_target_policy_cannot_be_relabelled(self):
        for invalid in (None, True, float('nan'), 1199):
            snapshot = sample_snapshot()
            snapshot['reference_age_seconds'] = invalid
            self.assertTrue(any('reference_age_seconds' in error for error in validate_snapshot(snapshot)))
        snapshot = sample_snapshot()
        del snapshot['target_policy']
        self.assertTrue(any('Original reference-hour targets' in error for error in validate_snapshot(snapshot)))

    def test_v2_receipt_freshness_uses_actual_issuance(self):
        snapshot = sample_snapshot(issued_delay_seconds=10800, receipt_age_seconds=3600)
        self.assertEqual(validate_snapshot(snapshot), [])
        snapshot['sources'][0]['available_at'] = '2026-01-01T13:59:59.999999-03:00'
        self.assertTrue(any('receipt is stale' in error for error in validate_snapshot(snapshot)))

    def test_legacy_v1_preserves_original_hour_and_receipt_freshness_rules(self):
        snapshot = sample_snapshot()
        snapshot['contract_id'] = LEGACY_FEATURE_CONTRACT_ID
        del snapshot['reference_age_seconds']
        del snapshot['target_policy']
        # A legacy NWP receipt was allowed to precede reference by up to 1h,
        # even if it was older than 1h when this historical receipt was issued.
        snapshot['sources'][-1]['available_at'] = '2026-01-01T11:00:00-03:00'
        original = copy.deepcopy(snapshot)
        self.assertEqual(validate_snapshot(snapshot), [])
        self.assertEqual(snapshot, original)
        snapshot['issued_at'] = '2026-01-01T13:00:00-03:00'
        self.assertTrue(any('in its reference hour' in error for error in validate_snapshot(snapshot)))
        snapshot['issued_at'] = original['issued_at']
        snapshot['sources'][-1]['available_at'] = '2026-01-01T10:59:59.999999-03:00'
        self.assertTrue(any('receipt is stale' in error for error in validate_snapshot(snapshot)))

    def test_unknown_contract_is_not_accepted_as_legacy(self):
        snapshot = sample_snapshot()
        snapshot['contract_id'] = 'radar-180-contemporaneous/v0'
        self.assertTrue(any('Wrong feature contract' in error for error in validate_snapshot(snapshot)))

    def test_bad_current_hour_and_names_rejected(self):
        snapshot = sample_snapshot()
        snapshot['sources'][0]['observed_through'] = '2026-01-01T11:45:00-03:00'
        snapshot['feature_names'][0], snapshot['feature_names'][1] = snapshot['feature_names'][1], snapshot['feature_names'][0]
        errors = validate_snapshot(snapshot)
        self.assertTrue(any('exact reference' in message for message in errors))
        self.assertTrue(any('names/order' in message for message in errors))

    def test_future_receipt_and_missing_sources_fail_closed(self):
        snapshot = sample_snapshot()
        snapshot['sources'][0]['available_at'] = '2026-01-01T12:21:00-03:00'
        snapshot['sources'].pop()
        errors = validate_snapshot(snapshot)
        self.assertTrue(any('received after issuance' in message for message in errors))
        self.assertTrue(any('required source receipt missing' in message for message in errors))

    def test_current_forecast_cannot_be_replaced_by_previous_day_product(self):
        snapshot = sample_snapshot()
        snapshot['sources'][-1].update(product='historical_forecast', field='precipitation_previous_day1')
        self.assertTrue(any('no previous_day1' in message for message in validate_snapshot(snapshot)))

    def test_missing_finite_and_coverage_checks(self):
        for bad in [None, float('nan'), float('inf'), True]:
            snapshot = sample_snapshot()
            snapshot['features'][122] = bad
            self.assertTrue(any('missing/non-finite' in message for message in validate_snapshot(snapshot)))
        snapshot = sample_snapshot()
        snapshot['input_readiness']['rainCoverage']['Carreiro'] = .49
        self.assertTrue(any('coverage below 50%' in message for message in validate_snapshot(snapshot)))

    def test_anchor_and_flow_values_must_match_readiness(self):
        snapshot = sample_snapshot()
        snapshot['features'][0] += .1
        snapshot['features'][25] += .1
        errors = validate_snapshot(snapshot)
        self.assertTrue(any('anchor differs' in message for message in errors))
        self.assertTrue(any('flow feature differs' in message for message in errors))

    def test_malformed_readiness_reports_missing_data(self):
        snapshot = sample_snapshot()
        snapshot['input_readiness']['levels'] = None
        self.assertTrue(any('levels must be an object' in message for message in validate_snapshot(snapshot)))

    def test_current_nwp_windows_exact_order_and_zero_valid(self):
        ref = datetime.fromisoformat('2026-01-01T12:00:00-03:00')
        location = dict(utc_offset_seconds=-10800, hourly_units={'precipitation': 'mm'},
                        hourly={'time': [(ref + timedelta(hours=h)).replace(tzinfo=None).isoformat() for h in range(1, 13)],
                                'precipitation': list(range(1, 13))})
        forecasts = {model: [copy.deepcopy(location) for _ in GROUPS] for model in NWP_MODELS}
        result = current_nwp_features(forecasts, ref.isoformat())
        self.assertEqual(result, [6., 21., 45., 78.] * 15)
        forecasts[NWP_MODELS[0]][0]['hourly']['precipitation'] = [0.] * 12
        self.assertEqual(current_nwp_features(forecasts, ref.isoformat())[:4], [0.] * 4)
        forecasts[NWP_MODELS[0]][0]['hourly']['precipitation'][0] = None
        with self.assertRaises(ContractError):
            current_nwp_features(forecasts, ref.isoformat())

    def test_observation_requires_exact_station_datum_and_receipt_cutoff(self):
        snapshot = sample_snapshot()
        label = sample_label(snapshot)
        arguments = dict(station_id=label['station_id'], datum_id=label['datum_id'],
                         valid_at=label['valid_at'], known_at=label['available_at'])
        self.assertEqual(select_exact_observation([label], **arguments), label)
        for changed in [{'station_id': '86720000'}, {'datum_id': 'another-gauge-reference'},
                        {'valid_at': '2026-01-01T13:15:00-03:00'}, {'known_at': label['valid_at']}]:
            with self.assertRaises(ContractError):
                select_exact_observation([label], **{**arguments, **changed})

    def test_later_invalid_revision_cannot_fall_back_to_approved_value(self):
        label = sample_label(sample_snapshot())
        invalid = {**label, 'quality': 'rejected', 'available_at': '2026-01-01T14:00:00-03:00'}
        with self.assertRaises(ContractError):
            select_exact_observation([label, invalid], station_id=label['station_id'], datum_id=label['datum_id'],
                                     valid_at=label['valid_at'], known_at=invalid['available_at'])

    def test_label_without_source_receipt_is_not_admissible(self):
        label = sample_label(sample_snapshot())
        del label['receipt_sha256']
        with self.assertRaisesRegex(ContractError, 'receipt SHA256'):
            select_exact_observation([label], station_id=label['station_id'], datum_id=label['datum_id'],
                                     valid_at=label['valid_at'], known_at=label['available_at'])


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.snapshots = [sample_snapshot(f'2026-01-{day:02}T12:00:00-03:00') for day in (1, 3, 5)]
        self.labels = [sample_label(snapshot) for snapshot in self.snapshots]
        self.plan = sample_plan()

    def build(self):
        return build_dataset(self.snapshots, self.labels, self.plan)

    def test_three_causal_splits_do_not_certify_or_promote(self):
        dataset = self.build()
        self.assertTrue(dataset['summary']['experiment_ready'])
        self.assertFalse(dataset['summary']['promotion_allowed'])
        self.assertEqual(dataset['summary']['validation_status'], 'not_evaluated')
        self.assertEqual([row['split'] for row in dataset['rows']], ['train', 'validation', 'test'])
        self.assertAlmostEqual(dataset['rows'][0]['actual_lead_h'], 2 / 3)
        self.assertEqual(dataset['rows'][0]['nominal_lead_h'], 1)

    def test_legacy_snapshot_is_preserved_but_not_relabelled_as_v2_training(self):
        legacy = self.snapshots[0]
        legacy['contract_id'] = LEGACY_FEATURE_CONTRACT_ID
        del legacy['reference_age_seconds']
        del legacy['target_policy']
        self.assertEqual(validate_snapshot(legacy), [])
        dataset = self.build()
        self.assertEqual(dataset['summary']['rejection_counts']['unsupported_training_contract'], 1)
        self.assertFalse(dataset['summary']['experiment_ready'])
        self.assertTrue(all(row['contract_id'] == FEATURE_CONTRACT_ID for row in dataset['rows']))
        self.assertEqual(legacy['contract_id'], LEGACY_FEATURE_CONTRACT_ID)

    def test_training_label_published_after_cutoff_is_excluded(self):
        self.labels[0]['available_at'] = self.plan['train_end']
        dataset = self.build()
        self.assertFalse(dataset['summary']['experiment_ready'])
        self.assertEqual(dataset['summary']['rejection_counts']['exact_label_unavailable'], 1)
        self.assertTrue(any('train/1h: 0 rows' in message for message in dataset['summary']['insufficient_data']))

    def test_target_at_event_or_split_end_is_purged(self):
        self.snapshots[0] = sample_snapshot('2026-01-02T23:00:00-03:00')
        self.labels[0] = sample_label(self.snapshots[0])
        dataset = self.build()
        self.assertEqual(dataset['summary']['rejection_counts']['purged_target_crosses_event_or_split'], 1)
        self.assertEqual(len(dataset['rows']), 2)

    def test_cross_split_event_rejected_before_build(self):
        self.plan['events'][0]['end_at'] = '2026-01-03T01:00:00-03:00'
        with self.assertRaises(ContractError):
            self.build()

    def test_duplicate_copies_and_revisions_do_not_multiply_training_rows(self):
        self.snapshots.append(copy.deepcopy(self.snapshots[0]))
        revised = copy.deepcopy(self.snapshots[0])
        revised['issued_at'] = '2026-01-01T12:30:00-03:00'
        revised['reference_age_seconds'] = 1800
        revised['features'][1] = .01
        self.snapshots.append(revised)
        dataset = self.build()
        self.assertEqual(len(dataset['rows']), 3)
        self.assertEqual(dataset['rows'][0]['issued_at'], revised['issued_at'])
        self.assertEqual(dataset['summary']['rejection_counts']['duplicate_snapshot'], 1)
        self.assertEqual(dataset['summary']['rejection_counts']['superseded_same_reference'], 1)

    def test_delayed_reference_excludes_elapsed_targets_without_renumbering(self):
        self.snapshots = [sample_snapshot(f'2026-01-{day:02}T12:00:00-03:00',
                                          issued_delay_seconds=10800) for day in (1, 3, 5)]
        self.plan['nominal_horizons_hours'] = [1, 3, 4, 6]
        self.labels = [sample_label(snapshot, lead) for snapshot in self.snapshots for lead in (1, 3, 4, 6)]
        dataset = self.build()
        self.assertEqual(dataset['summary']['rejection_counts']['target_elapsed_at_issuance'], 6)
        self.assertEqual(len(dataset['rows']), 6)
        for row in dataset['rows']:
            self.assertIn(row['nominal_lead_h'], (4, 6))
            self.assertEqual(row['actual_lead_h'], row['nominal_lead_h'] - 3)
            reference = datetime.fromisoformat(row['reference_at'])
            target = datetime.fromisoformat(row['target_at'])
            self.assertEqual((target - reference).total_seconds(), row['nominal_lead_h'] * 3600)

    def test_missing_holdout_or_event_diversity_blocks_experiment(self):
        self.plan['minimum_events_per_split']['test'] = 2
        dataset = self.build()
        self.assertFalse(dataset['summary']['experiment_ready'])
        self.assertIn('test/1h: 1 events below required 2', dataset['summary']['insufficient_data'])

    def test_exact_label_other_datum_is_not_used(self):
        self.labels[-1]['datum_id'] = 'different-reference'
        dataset = self.build()
        self.assertFalse(dataset['summary']['experiment_ready'])
        self.assertEqual(dataset['summary']['rejection_counts']['exact_label_unavailable'], 1)

    def test_cli_writes_new_local_artifacts_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, value in [('snapshots', self.snapshots), ('observations', self.labels), ('plan', self.plan)]:
                (root / (name + '.json')).write_text(json.dumps(value))
            output = root / 'dataset'
            command = [sys.executable, '-B', str(Path(__file__).with_name('hydro_snapshot_dataset.py')),
                       '--snapshots', str(root / 'snapshots.json'), '--observations', str(root / 'observations.json'),
                       '--plan', str(root / 'plan.json'), '--output', str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(len(json.loads((output / 'input-manifest.json').read_text())), 3)
            before = (output / 'dataset.json').read_bytes()
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual((output / 'dataset.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
