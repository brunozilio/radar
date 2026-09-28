"""Causal rain alignment and bounded nonnegative response invariants."""
import unittest

import numpy as np

from hydro_rain_runoff_residual import (
    GROUPS, WINDOWS, UPLIFT_CAP_M, bounded_uplift,
    fit_nonnegative_ridge, rain_age_matrix,
)


class RainRunoffResidualTests(unittest.TestCase):
    def archive(self):
        quarter = np.arange(0, 27*3600+1, 900, dtype=float)
        data = {'times': quarter}
        for group in GROUPS:
            for window in WINDOWS:
                data[f'{group}:rain{window}'] = np.zeros(len(quarter))
                data[f'{group}:cover{window}'] = np.ones(len(quarter))
        return data

    def test_rain_ends_one_hour_before_origin_and_uses_disjoint_ages(self):
        archive = self.archive()
        earlier = 24*4
        future = 25*4
        for window, amount in zip(WINDOWS, (12, 20, 30, 40)):
            archive[f'Baixo Antas:rain{window}'][earlier] = amount
            archive[f'Baixo Antas:rain{window}'][future] = 1000
        features, raw, names, valid = rain_age_matrix(np.array([25*3600.0]), archive)
        self.assertTrue(valid[0])
        np.testing.assert_allclose(raw[0, :4], (12, 8, 10, 10))
        np.testing.assert_allclose(features[0, :4], (.12, .08, .10, .10))
        self.assertEqual(len(names), 20)

    def test_incomplete_rain_never_becomes_zero(self):
        archive = self.archive()
        archive['Carreiro:cover12'][24*4] = .49
        _, _, _, valid = rain_age_matrix(np.array([25*3600.0]), archive)
        self.assertFalse(valid[0])

    def test_nonnegative_response_and_hard_cap(self):
        x = np.eye(2)
        y = np.array([-1.0, 20.0])
        beta = fit_nonnegative_ridge(x, y, np.arange(2), alpha=10)
        self.assertEqual(beta[0], 0)
        self.assertGreater(beta[1], 0)
        result = bounded_uplift(np.array([[0., 0.], [0., 100.]]), beta)
        np.testing.assert_allclose(result, [0, UPLIFT_CAP_M])


if __name__ == '__main__':
    unittest.main()
