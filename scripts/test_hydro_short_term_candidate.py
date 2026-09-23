import copy
import json
import unittest

from hydro_short_term_candidate import build_shadow


def fixture():
    anchor = dict(timestamp='2026-09-22T12:00:00-03:00', level=15.0,
                  received_at='2026-09-22T12:10:00-03:00', station='86510000',
                  quality='approved', evidence_id='anchor-source-sha')
    past = {**anchor, 'timestamp': '2026-09-22T11:00:00-03:00', 'level': 15.6,
            'received_at': '2026-09-22T11:10:00-03:00', 'evidence_id': 'past-source-sha'}
    return dict(reference_at=anchor['timestamp'], issued_at='2026-09-22T12:30:00-03:00',
                anchor=anchor, received_history=[past], baseline_points=[
                    {'timestamp': f'2026-09-22T{hour}:30:00-03:00', 'level': 14.8}
                    for hour in range(13, 17)])


class ShortTermCandidateTest(unittest.TestCase):
    def test_formula_real_leads_and_long_leads_unchanged(self):
        result = build_shadow(**fixture())
        self.assertEqual(result['status'], 'shadow_generated')
        self.assertEqual(result['directionKnownAtIssue'], 'falling')
        self.assertEqual([p['weight'] for p in result['points']], [.5, .25, 0, 0])
        self.assertAlmostEqual(result['points'][0]['shadowLevel'], 14.45)
        self.assertEqual(result['points'][2]['shadowLevel'], 14.8)
        self.assertEqual(result['points'][3]['shadowLevel'], 14.8)
        self.assertFalse(result['publishable'])
        self.assertFalse(result['goalEvidenceEligible'])

    def test_original_inputs_are_unchanged(self):
        inputs = fixture()
        saved = copy.deepcopy(inputs)
        build_shadow(**inputs)
        self.assertEqual(inputs, saved)

    def test_missing_exact_hour_does_not_interpolate(self):
        inputs = fixture()
        inputs['received_history'][0]['timestamp'] = '2026-09-22T10:45:00-03:00'
        self.assert_unavailable(inputs)

    def test_future_receipt_is_not_used(self):
        inputs = fixture()
        inputs['received_history'][0]['received_at'] = '2026-09-22T12:31:00-03:00'
        self.assert_unavailable(inputs)

    def test_anchor_must_be_exact_reference(self):
        inputs = fixture()
        inputs['anchor']['timestamp'] = '2026-09-22T11:45:00-03:00'
        self.assert_unavailable(inputs)

    def test_issued_after_reference_hour_is_unavailable(self):
        inputs = fixture()
        inputs['issued_at'] = '2026-09-22T13:00:00-03:00'
        self.assert_unavailable(inputs)

    def test_missing_quality_and_legacy_are_blocked_by_default(self):
        for quality in (None, 'rejected', 'legacy_unverified'):
            inputs = fixture()
            inputs['received_history'][0]['quality'] = quality
            self.assert_unavailable(inputs)

    def test_explicit_research_legacy_exception_is_labeled(self):
        inputs = fixture()
        inputs['received_history'][0]['quality'] = 'legacy_unverified'
        result = build_shadow(**inputs, allow_legacy_unverified=True)
        self.assertEqual(result['status'], 'shadow_generated')
        self.assertEqual(result['receiptEvidence'], 'legacy_created_at_unverified')
        self.assertFalse(result['goalEvidenceEligible'])

    def test_missing_evidence_is_blocked(self):
        inputs = fixture()
        del inputs['anchor']['evidence_id']
        self.assert_unavailable(inputs)

    def test_conflicting_duplicate_past_is_blocked(self):
        inputs = fixture()
        inputs['received_history'].append({**inputs['received_history'][0], 'level': 15.5})
        self.assert_unavailable(inputs)

    def test_identical_duplicate_is_recorded(self):
        inputs = fixture()
        inputs['received_history'].append(copy.deepcopy(inputs['received_history'][0]))
        result = build_shadow(**inputs)
        self.assertEqual(result['status'], 'shadow_generated')
        self.assertEqual(len(result['usedObservationEvidenceIds']), 3)

    def test_future_measurement_cannot_influence_candidate(self):
        inputs = fixture()
        before = build_shadow(**inputs)
        inputs['received_history'].append({**inputs['received_history'][0],
            'timestamp': '2026-09-22T14:00:00-03:00', 'level': 999.0,
            'received_at': '2026-09-22T14:10:00-03:00'})
        after = build_shadow(**inputs)
        self.assertEqual(before['points'], after['points'])
        self.assertNotEqual(before['inputSha256'], after['inputSha256'])

    def test_bad_value_unavailable_and_artifact_remains_serializable(self):
        for level in (None, True, -1, float('nan'), float('inf')):
            inputs = fixture()
            inputs['baseline_points'][-1]['level'] = level
            result = self.assert_unavailable(inputs)
            json.dumps(result, allow_nan=False)

    def test_correction_is_bounded_in_both_directions(self):
        for level in (0.0, 100.0):
            inputs = fixture()
            inputs['received_history'][0]['level'] = level
            result = build_shadow(**inputs)
            self.assertEqual(abs(result['points'][0]['correctionM']), .5)
            self.assertTrue(result['points'][0]['correctionWasCapped'])

    def test_zero_and_elapsed_lead_unavailable(self):
        for target in ('2026-09-22T12:30:00-03:00', '2026-09-22T12:00:00-03:00'):
            inputs = fixture()
            inputs['baseline_points'][0]['timestamp'] = target
            self.assert_unavailable(inputs)

    def test_timezone_required_and_station_cannot_be_relabeled(self):
        inputs = fixture()
        inputs['reference_at'] = '2026-09-22T12:00:00'
        self.assert_unavailable(inputs)
        inputs = fixture()
        inputs['station'] = '86720000'
        self.assert_unavailable(inputs)

    def test_duplicate_target_and_empty_baseline_unavailable(self):
        inputs = fixture()
        inputs['baseline_points'].append(copy.deepcopy(inputs['baseline_points'][0]))
        self.assert_unavailable(inputs)
        inputs['baseline_points'] = []
        self.assert_unavailable(inputs)

    def test_deterministic_evidence_hash(self):
        self.assertEqual(build_shadow(**fixture()), build_shadow(**fixture()))

    def assert_unavailable(self, inputs):
        result = build_shadow(**inputs)
        self.assertEqual(result['status'], 'unavailable')
        self.assertTrue(result['reasons'])
        self.assertEqual(result['points'], [])
        self.assertFalse(result['publishable'])
        return result


if __name__ == '__main__':
    unittest.main()
