import unittest
from hydro_verification_metrics import error_metrics,diagnostic_scorecard


def row(**kwargs):
    return {'forecast_m':8.5,'observed_m':8.,'valid_at':'2026-09-21T18:00:00-03:00','flood_event_id':'one-event','evidence_kind':'forecast_issue','model_id':'radar','model_version':'v1','minimum_verified_lead_h':1,'status':'matched','goal_eligible':False,'exclusion_reasons':'datum_unverified',**kwargs}


class VerificationMetricsTests(unittest.TestCase):
    def test_signed_bias_quantiles_and_repeated_targets(self):
        result=error_metrics([row(),row(forecast_m=6.5)])
        self.assertEqual(result['mae_m'],1.)
        self.assertEqual(result['bias_m'],-.5)
        self.assertEqual(result['accuracy_percent'],50.)
        self.assertAlmostEqual(result['p90_abs_m'],1.4)
        self.assertAlmostEqual(result['p98_abs_m'],1.48)
        self.assertEqual(result['unique_target_times'],1)
        self.assertEqual(result['observed_flood_clusters'],1)
        self.assertIsNone(result['confidence_interval'])

    def test_archives_and_unverified_data_never_become_eligible(self):
        result=diagnostic_scorecard([row(),row(evidence_kind='archival_forecast_import')])
        self.assertEqual(len(result),4)
        self.assertTrue(all(r['n']==1 and r['goal_eligible_n']==0 for r in result))
        self.assertTrue(all(not r['goal_achieved'] for r in result))

    def test_missing_truth_retains_denominator_status_without_scoring_a_hit(self):
        result=diagnostic_scorecard([row(observed_m=None,status='missing_exact_observation')])
        self.assertTrue(all(r['n']==0 and r['accuracy_percent'] is None for r in result))
        self.assertEqual(result[0]['status_counts_in_model_horizon'],{'missing_exact_observation':1})

    def test_low_water_does_not_dilute_high_water_error(self):
        result=diagnostic_scorecard([row(forecast_m=10),row(forecast_m=3,observed_m=3)])
        self.assertEqual(next(r for r in result if r['regime']=='all')['accuracy_percent'],50)
        self.assertEqual(next(r for r in result if r['regime']=='level_ge_7m')['accuracy_percent'],0)
