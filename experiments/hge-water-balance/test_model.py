"""Physical and numerical checks for the copied HGE routine and its adapter."""
import unittest

import numpy as np

from run import initial_state, parameters, simulate, simulate_series, upstream


class WaterBalanceTest(unittest.TestCase):
    def setUp(self):
        self.x = np.array([150., .3, 1.2, 3., 30., .5])
        self.area = 1273.3799363219698

    def test_compiled_matches_original_without_corrupting_saved_states(self):
        rain = np.array([0., 4., 35., 70., 0., 0., 1.])
        initial = initial_state(self.x)
        expected = []
        state = initial.copy()
        for p in rain:
            state = upstream.rainfall_runoff(state.copy(), parameters(self.x), p, 3 / 24., self.area, 3600.)
            expected.append(state.copy())
        actual, mass_errors = simulate(rain, 3., self.x, self.area, initial)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-10)
        np.testing.assert_array_equal(initial, initial_state(self.x))
        self.assertLess(np.max(abs(mass_errors)), 1e-10)

    def test_impulse_conserves_total_water_and_area_conversion(self):
        rain = np.zeros(2400)
        rain[0] = 120.
        initial = np.zeros(6)
        states, errors = simulate(rain, 0., self.x, self.area, initial)
        total_out_mm = states[:, -1].sum() * 3600. / (self.area * 1000.)
        self.assertAlmostEqual(total_out_mm + states[-1, :-1].sum(), 120., places=8)
        self.assertGreaterEqual(states.min(), 0.)
        self.assertLess(np.max(abs(errors)), 1e-9)
        doubled, _ = simulate(rain, 0., self.x, self.area * 2, initial)
        np.testing.assert_allclose(doubled[:, -1], 2 * states[:, -1])

    def test_restart_is_identical_and_future_rain_cannot_change_past(self):
        rain = np.r_[np.zeros(10), np.full(8, 20.), np.zeros(100)]
        whole, _ = simulate(rain, 3., self.x, self.area, initial_state(self.x))
        past, _ = simulate(rain[:15], 3., self.x, self.area, initial_state(self.x))
        saved_past = past.copy()
        future, _ = simulate(rain[15:], 3., self.x, self.area, past[-1])
        np.testing.assert_array_equal(saved_past, past)
        np.testing.assert_allclose(np.vstack([past, future]), whole)
        altered = rain.copy()
        altered[15:] += 50
        changed, _ = simulate(altered, 3., self.x, self.area, initial_state(self.x))
        np.testing.assert_array_equal(changed[:15], whole[:15])

    def test_wet_soil_generates_more_immediate_runoff(self):
        dry = np.zeros(6)
        wet = np.zeros(6)
        wet[0] = self.x[0]
        dry_result, _ = simulate(np.array([30.]), 0., self.x, self.area, dry)
        wet_result, _ = simulate(np.array([30.]), 0., self.x, self.area, wet)
        self.assertGreater(wet_result[-1, -1], dry_result[-1, -1])

    def test_variable_et0_matches_original_hour_by_hour(self):
        rain = np.array([0., 8., 40., 0.])
        pet = np.array([0., .05, .2, .7])
        state = initial_state(self.x)
        expected = []
        for p, et in zip(rain, pet):
            state = upstream.rainfall_runoff(state.copy(), parameters(self.x), p, et, self.area, 3600.)
            expected.append(state.copy())
        actual, errors = simulate_series(rain, pet, self.x, self.area, initial_state(self.x))
        np.testing.assert_allclose(actual, expected)
        self.assertLess(np.max(abs(errors)), 1e-9)

    def test_unknown_et0_cannot_silently_propagate_nan(self):
        with self.assertRaises(ValueError):
            simulate_series(np.zeros(2), np.array([.1, np.nan]), self.x, self.area, initial_state(self.x))
        with self.assertRaises(ValueError):
            simulate_series(np.zeros(2), np.zeros(1), self.x, self.area, initial_state(self.x))


if __name__ == "__main__":
    unittest.main()
