import unittest
from hydro_accuracy_scorecard import summarize


def row(**kw):
    return {'model':'reference','phase':'test','lead_h':'1','origin':'2026-09-21T15:00:00-03:00',
            'target_time':'2026-09-21T16:00:00-03:00','base_m':'6','actual_m':'7','forecast_m':'7.5',**kw}


class AccuracyTests(unittest.TestCase):
    def test_threshold_and_flood_do_not_get_diluted_by_low_water(self):
        data=[row(),row(origin='2026-09-21T16:00:00-03:00',target_time='2026-09-21T17:00:00-03:00',forecast_m='8'),
              row(origin='2026-09-21T17:00:00-03:00',target_time='2026-09-21T18:00:00-03:00',actual_m='3',forecast_m='3')]
        result=summarize(data)
        high=next(r for r in result if r['regime']=='level_ge_7m')
        self.assertEqual(high['accuracy_percent'],50)
        self.assertEqual(high['n'],2)
        self.assertFalse(high['goal_prospectively_verified'])

    def test_duplicate_and_wrong_horizon_rejected(self):
        with self.assertRaises(ValueError):summarize([row(),row()])
        with self.assertRaises(ValueError):summarize([row(lead_h='12')])

    def test_missing_truth_is_not_success(self):
        result=summarize([row(actual_m='nan')])
        self.assertEqual(result[0]['n'],0)
        self.assertIsNone(result[0]['accuracy_percent'])
        self.assertEqual(result[0]['invalid_pairs_in_model_horizon'],1)


if __name__=='__main__':unittest.main()
