"""Causal timestamp and missing-rain checks for the rain leading-signal study."""
import unittest

import numpy as np

from hydro_rain_leading_experiment import GROUPS, WINDOWS, rain_matrix


class RainMatrixTests(unittest.TestCase):
    def test_uses_only_rain_ending_an_hour_before_origin(self):
        times = np.arange(0, 4 * 3600, 900, dtype=float)
        archive = {'times': times}
        for group in GROUPS:
            for window in WINDOWS:
                archive[f'{group}:rain{window}'] = np.arange(len(times), dtype=float)
                archive[f'{group}:cover{window}'] = np.ones(len(times))
        origins = np.array([3600., 7200., 10800., 18000.])
        features, _, complete = rain_matrix(origins, archive)
        self.assertEqual(complete.tolist(), [True, True, True, False])
        self.assertEqual(features[0, 0], 0.)
        self.assertEqual(features[1, 0], 4 / 100)
        self.assertEqual(features[2, 0], 8 / 100)
        self.assertTrue(np.isnan(features[3]).all())

    def test_missing_coverage_never_becomes_zero_rain(self):
        times = np.arange(0, 3 * 3600, 900, dtype=float)
        archive = {'times': times}
        for group in GROUPS:
            for window in WINDOWS:
                archive[f'{group}:rain{window}'] = np.zeros(len(times))
                archive[f'{group}:cover{window}'] = np.ones(len(times))
        archive['Carreiro:cover6'][4] = .49
        features, _, complete = rain_matrix(np.array([3600., 7200.]), archive)
        self.assertEqual(complete.tolist(), [True, False])
        self.assertTrue(np.isnan(features[1, 5]))


if __name__ == '__main__':
    unittest.main()
