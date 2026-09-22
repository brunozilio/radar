import unittest
import hashlib
import tempfile
from pathlib import Path
from hydro_reservoir_stratification import origin_trend, verify_prediction_hash


class TrendTest(unittest.TestCase):
    def test_preserved_predictions_must_match_either_manifest_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'predictions.csv'
            path.write_bytes(b'original predictions')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifests = [{path.name: digest}, [{'file': path.name, 'sha256': digest}]]
            for manifest in manifests:
                verify_prediction_hash(path, manifest)
            path.write_bytes(b'altered predictions')
            for manifest in manifests + [{}, []]:
                with self.assertRaises(ValueError):
                    verify_prediction_hash(path, manifest)

    def test_future_values_do_not_define_past_trend(self):
        origin = 20000
        values = {origin-900: 7.6, origin-11700: 7., origin: 1., origin+3600: 20.}
        observations = {t: {'quality': 'Dado aprovado', 'level_m': v} for t, v in values.items()}
        self.assertEqual(origin_trend(origin, observations, values)[0], 'rising')
        observations[origin-900]['quality'] = 'Dado suspeito'
        self.assertEqual(origin_trend(origin, observations, values), ('unknown', None))

    def test_mismatching_or_missing_endpoint_is_unknown(self):
        obs = {1100: {'quality': 'Dado aprovado', 'level_m': 7.}, -9700: {'quality': 'Dado aprovado', 'level_m': 7.}}
        self.assertEqual(origin_trend(2000, obs, {1100: 7., -9700: 6.}), ('unknown', None))
        self.assertEqual(origin_trend(2000, obs, {1100: 7., -9700: 7.}), ('stable', 0.))

    def test_threshold_boundary_is_stable(self):
        values = {1100: 7.15, -9700: 7.}
        obs = {t: {'quality': 'Dado aprovado', 'level_m': v} for t, v in values.items()}
        self.assertEqual(origin_trend(2000, obs, values)[0], 'stable')


if __name__ == '__main__': unittest.main()
