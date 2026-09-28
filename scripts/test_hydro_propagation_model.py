"""Causality, missing-data and frozen-model regression tests."""
import copy
import json
import unittest

import numpy as np

from hydro_propagation_model import (
    CONTRACT, EMBARGO_HOURS, FLOWS, REQUIRED, SOURCES, TARGET,
    IncompleteHydrometry, calibrate_lags, epoch, feature_matrix, fit_model,
    predict, shift, split_rows, validate_series,
)


def synthetic(n=850):
    rng = np.random.default_rng(1923)
    times = epoch("2025-01-01T00:00:00+00:00") + np.arange(n) * 3600
    source_changes = rng.normal(0, .055, n)
    source = 5 + np.cumsum(source_changes)
    local_changes = .75 * np.nan_to_num(shift(source_changes, 8)) + rng.normal(0, .003, n)
    local = 5 + np.cumsum(local_changes)
    data = {TARGET: local}
    for index, key in enumerate(SOURCES):
        data[key] = (source * 400 + 200) if key in FLOWS else source + index / 20
    return times, data


class PropagationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.times, cls.data = synthetic()
        cls.cuts = (cls.times[350], cls.times[610], cls.times[760])
        cls.model, cls.report, cls.predictions = fit_model(cls.times, cls.data, *cls.cuts)

    def test_timestamp_requires_timezone(self):
        with self.assertRaises(ValueError):
            epoch("2026-09-23T08:00:00")

    def test_exact_hour_grid_does_not_accept_shifted_or_missing_hours(self):
        with self.assertRaises(ValueError):
            validate_series(self.times + 900, self.data)
        with self.assertRaises(ValueError):
            validate_series(np.delete(self.times, 20), {k: np.delete(v, 20) for k, v in self.data.items()})

    def test_lag_is_identified_from_training_differences_only(self):
        before, _ = calibrate_lags(self.times, self.data, self.cuts[0])
        self.assertEqual(before["86472000:H"]["lagHours"], 8)
        after_data = {key: value.copy() for key, value in self.data.items()}
        for key in after_data:
            after_data[key][self.times >= self.cuts[0]] += np.arange((self.times >= self.cuts[0]).sum()) * 300
        after, _ = calibrate_lags(self.times, after_data, self.cuts[0])
        self.assertEqual(before, after)

    def test_future_targets_and_predictor_windows_do_not_cross_split_boundaries(self):
        rows = split_rows(self.times, np.ones(len(self.times), dtype=bool), 6, *self.cuts)
        self.assertTrue(np.all(self.times[rows["train"]] + 6 * 3600 < self.cuts[0]))
        self.assertTrue(np.all(self.times[rows["validation"]] >= self.cuts[0] + EMBARGO_HOURS * 3600))
        self.assertTrue(np.all(self.times[rows["validation"]] + 6 * 3600 < self.cuts[1]))
        self.assertTrue(np.all(self.times[rows["test"]] >= self.cuts[1] + EMBARGO_HOURS * 3600))
        self.assertEqual(self.times[rows["stress_current"][0]], self.cuts[2])

    def test_frozen_model_is_json_portable_and_rain_independent(self):
        model = json.loads(json.dumps(self.model, allow_nan=False))
        self.assertEqual(model["contract"], CONTRACT)
        self.assertFalse(model["rainRequired"])
        self.assertFalse(model["promotionEligible"])
        self.assertFalse(model["historicalAvailabilityReconstructed"])
        for row in model["horizons"]:
            self.assertFalse(any("rain" in name or "chuva" in name for name in row["featureNames"]))
        output = predict(model, self.times, self.data, self.times[-1], self.times[-1] + 900)
        self.assertEqual(len(output["points"]), 6)
        self.assertFalse(output["publishable"])

    def test_test_period_cannot_change_lags_parameters_or_selection(self):
        altered = {key: value.copy() for key, value in self.data.items()}
        for key in altered:
            altered[key][self.times >= self.cuts[1]] += 30
        other, _, _ = fit_model(self.times, altered, *self.cuts)
        self.assertEqual(self.model["lags"], other["lags"])
        for first, second in zip(self.model["horizons"], other["horizons"]):
            self.assertEqual(first["parameters"], second["parameters"])
            self.assertEqual(first["validationScore"], second["validationScore"])
            self.assertEqual(first["family"], second["family"])

    def test_every_family_and_baseline_use_same_observed_origins(self):
        for horizon in range(1, 7):
            for phase in ("validation", "test", "stress_current"):
                groups = []
                for family in ("contemporaneous", "lagged", "persistence", "local_trend_2h"):
                    groups.append({row["origin"] for row in self.predictions if row["h"] == horizon and row["phase"] == phase and row["model"] == family})
                self.assertTrue(all(group == groups[0] for group in groups))

    def test_future_observations_cannot_change_forecast(self):
        reference = self.times[-20]
        before = predict(self.model, self.times, self.data, reference, reference + 600)
        altered = {key: values.copy() for key, values in self.data.items()}
        for key in altered:
            altered[key][self.times > reference] = 9876
        after = predict(self.model, self.times, altered, reference, reference + 600)
        self.assertEqual(before, after)

    def test_missing_current_flow_blocks_even_if_lagged_flow_exists(self):
        data = {key: values.copy() for key, values in self.data.items()}
        data["julho:Q"][-1] = np.nan
        with self.assertRaisesRegex(IncompleteHydrometry, "julho:Q"):
            predict(self.model, self.times, data, self.times[-1], self.times[-1] + 1)

    def test_missing_exact_historical_observation_is_not_carried_forward(self):
        data = {key: values.copy() for key, values in self.data.items()}
        data[TARGET][-3] = np.nan
        with self.assertRaisesRegex(IncompleteHydrometry, "slope2"):
            predict(self.model, self.times, data, self.times[-1], self.times[-1] + 1)

    def test_delay_keeps_only_original_future_targets_and_nominal_leads(self):
        reference = self.times[-1]
        result = predict(self.model, self.times, self.data, reference, reference + 2.5 * 3600)
        self.assertEqual(result["forecastStartLeadHours"], 3)
        self.assertEqual([row["nominalLeadHours"] for row in result["points"]], [3, 4, 5, 6])
        self.assertEqual([row["realLeadHours"] for row in result["points"]], [.5, 1.5, 2.5, 3.5])
        for row in result["points"]:
            self.assertEqual(epoch(row["time"]), reference + row["nominalLeadHours"] * 3600)

    def test_reference_must_be_observed_and_at_most_three_hours_old(self):
        with self.assertRaises(ValueError):
            predict(self.model, self.times, self.data, self.times[-1], self.times[-1] + 3 * 3600 + 1)
        with self.assertRaises(IncompleteHydrometry):
            predict(self.model, self.times, self.data, self.times[-1] + 3600, self.times[-1] + 3601)
        with self.assertRaises(ValueError):
            predict(self.model, self.times, self.data, self.times[-1], self.times[-1] - 1)

    def test_missing_model_horizon_is_not_a_partial_success(self):
        model = copy.deepcopy(self.model)
        model["horizons"].pop()
        with self.assertRaises(ValueError):
            predict(model, self.times, self.data, self.times[-1], self.times[-1] + 1)

    def test_negative_flow_is_missing_not_zero(self):
        data = {key: values.copy() for key, values in self.data.items()}
        data["castro:I"][-1] = -1
        with self.assertRaises(IncompleteHydrometry):
            predict(self.model, self.times, data, self.times[-1], self.times[-1] + 1)
        data["castro:I"][-1] = 0
        result = predict(self.model, self.times, data, self.times[-1], self.times[-1] + 1)
        self.assertEqual(len(result["points"]), 6)


if __name__ == "__main__":
    unittest.main()
