import unittest
import numpy as np
from hydro_reservoir_mucum_experiment import (route, anchor_index, score, fill_missing,
    fit_regional_proxy, anchor_delay_hours, reconstruct_anchor, residual_correction)


class EndToEndTest(unittest.TestCase):
    def test_residual_time_scale_preserves_initial_value_sign_and_zero(self):
        for tau in (2,6,12):
            self.assertEqual(residual_correction(100.,0,tau),100.)
            self.assertEqual(residual_correction(-100.,0,tau),-100.)
            self.assertAlmostEqual(residual_correction(100.,tau,tau),100./np.e)
            self.assertEqual(residual_correction(0.,12,tau),0.)
            self.assertLess(abs(residual_correction(-100.,12,tau)),100.)
        self.assertLess(residual_correction(100.,6,2),residual_correction(100.,6,6))
        self.assertLess(residual_correction(100.,6,6),residual_correction(100.,6,12))

    def test_invalid_time_constant_or_future_anchor_rejected(self):
        for tau in (0,-1,3,True,None,float('nan')):
            with self.assertRaises(ValueError):residual_correction(100.,1,tau)
        for elapsed in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):residual_correction(100.,elapsed,6)

    def test_future_truth_cannot_change_routing(self):
        a = np.array([10., 20., 30., 40., 50.]); b = a.copy(); b[2:] = np.nan
        args = ([100., 200.], [.25, .75], [1, 2], 2, 1)
        self.assertEqual(route(a, *args), 40.)
        self.assertEqual(route(a, *args), route(b, *args))

    def test_anchor_requires_exact_time(self):
        self.assertEqual(anchor_index(np.array([0., 900., 1800.]), 1800.), 1)
        self.assertIsNone(anchor_index(np.array([0., 1800.]), 1800.))

    def test_delay_selects_only_its_exact_past_measurement(self):
        grid = np.arange(0, 7201, 900)
        values = grid/3600*80+100  # Independent linear-flow reference.
        for minutes in (15, 30, 45):
            age = anchor_delay_hours(minutes)
            index = anchor_index(grid, 3600, minutes*60)
            self.assertEqual(grid[index], 3600-minutes*60)
            self.assertEqual(reconstruct_anchor(100., 180., age), values[index])
            # A later sample cannot stand in for the requested old anchor.
            self.assertIsNone(anchor_index(np.delete(grid, index), 3600, minutes*60))

    def test_unsupported_delay_cannot_extrapolate_or_use_future_anchor(self):
        for minutes in (True, 0, -15, 60, 90, float('nan'), '30'):
            with self.assertRaises(ValueError): anchor_delay_hours(minutes)
        for age in (0, -0.25, 1, 1.5, float('nan')):
            with self.assertRaises(ValueError): reconstruct_anchor(100., 180., age)

    def test_missing_endpoint_is_not_hidden_by_interpolation(self):
        for minutes in (15, 30, 45):
            self.assertTrue(np.isnan(reconstruct_anchor(np.nan, 180., anchor_delay_hours(minutes))))
            self.assertTrue(np.isnan(reconstruct_anchor(100., np.nan, anchor_delay_hours(minutes))))

    def test_zero_weight_does_not_require_a_value_but_tiny_weight_does(self):
        # The second historical sample has no contribution to the sum.
        args = ([np.nan, 20.], [100.], [1., 0.], [1, 2], 2, 0)
        self.assertTrue(np.isnan(route(*args)))
        self.assertEqual(route(*args, skip_zero_weights=True), 20.)
        self.assertTrue(np.isnan(route([np.nan, 20.], [100.], [1., 1e-15], [1, 2], 2, 0,
                                       skip_zero_weights=True)))

    def test_zero_weight_future_index_is_not_accessed(self):
        self.assertEqual(route([20.], [], [0., 1.], [1, 2], 1, 1,
                               skip_zero_weights=True), 20.)

    def test_proxy_never_replaces_observed_zero_or_mutates_source(self):
        source = np.array([0., 3., np.nan]); estimates = np.array([99., 99., 4.])
        np.testing.assert_equal(fill_missing(source, estimates), [0., 3., 4.])
        np.testing.assert_equal(source, [0., 3., np.nan])

    def test_proxy_training_ignores_future_targets_and_all_carreiro_inputs(self):
        rng = np.random.default_rng(22); X = rng.normal(size=(60, 53))
        times = np.arange(60)*3600.; y = np.arange(60)/100.
        a, _, train = fit_regional_proxy(X, times, y, 3, 40*3600.)
        altered = X.copy(); altered[:, 24:28] = 999.; changed_y = y.copy(); changed_y[40:] = 900.
        b, _, train2 = fit_regional_proxy(altered, times, changed_y, 3, 40*3600.)
        np.testing.assert_equal(train, train2); self.assertTrue(np.all(times[train]+3*3600 < 40*3600))
        for key in a: np.testing.assert_allclose(a[key], b[key], atol=0, rtol=0)

    def test_failed_forecast_is_in_coverage_and_50cm_is_inclusive(self):
        rows = [{'actual_m': 7., 'status': 'paired', 'reference_m': 7.5, 'julho_levels_m': 7.6},
                {'actual_m': 8., 'status': 'missing_exact_anchor', 'reference_m': None, 'julho_levels_m': None}]
        results = score(rows, True)
        self.assertEqual(results[0]['coverage'], .5)
        self.assertEqual(results[0]['within_0_50_fraction'], 1.)
        self.assertEqual(results[1]['within_0_50_fraction'], 0.)


if __name__ == '__main__': unittest.main()
