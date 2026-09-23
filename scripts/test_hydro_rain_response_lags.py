import copy
import unittest
import numpy as np
from hydro_rain_response_lags import PLAN, evaluate, epoch


class RainResponseLagTests(unittest.TestCase):
    def test_lag_selection_does_not_use_later_period_levels_or_rain(self):
        start = epoch('2025-09-01T00:00:00-03:00')
        times = start + np.arange(2000)*3600
        rng = np.random.default_rng(52)
        rain = rng.gamma(1, 2, len(times))
        levels = np.zeros(len(times)) + 10
        for i in range(10, len(times)):
            levels[i] = levels[i-3] + rain[i-7]
        baseline = evaluate(times, levels, {'fixture': rain})
        self.assertEqual(baseline['selected']['fixture']['lagHours'], 7)
        later = times >= epoch(PLAN['trainingEnd'])
        changed_levels, changed_rain = levels.copy(), rain.copy()
        changed_levels[later] = rng.uniform(0, 100, later.sum())
        changed_rain[later] = rng.uniform(0, 100, later.sum())
        revised = evaluate(times, changed_levels, {'fixture': changed_rain})
        self.assertEqual(revised['selected']['fixture']['lagHours'], 7)
        self.assertEqual(revised['allTrainingLagScores'], baseline['allTrainingLagScores'])

    def test_missing_or_dry_series_has_no_supported_lag(self):
        times = epoch('2025-09-01T00:00:00-03:00') + np.arange(500)*3600
        for values in (np.full(500, np.nan), np.zeros(500)):
            result = evaluate(times, np.arange(500, dtype=float), {'fixture': values})
            self.assertIsNone(result['selected']['fixture']['lagHours'])
            self.assertEqual(result['selected']['fixture']['status'], 'unsupported')


if __name__ == '__main__':
    unittest.main()
