import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np

from hydro_encantado import features, predict, read_levels, sample, STATIONS, TZ, ROOT, VERSION, MODEL_CONFIGS


class EncantadoTests(unittest.TestCase):
    def series(self):
        times = np.arange(0, 24 * 3600, 900, dtype=float)
        return {code: {'times': times, 'level': 4 + times / 36000} for code in STATIONS}

    def test_future_observations_do_not_change_features(self):
        series = self.series()
        before, anchor = features(series, np.array([12 * 3600]))
        for s in series.values():
            s['level'][s['times'] > 12 * 3600] = 1000
        after, next_anchor = features(series, np.array([12 * 3600]))
        np.testing.assert_array_equal(before, after)
        np.testing.assert_array_equal(anchor, next_anchor)

    def test_stale_missing_and_unobserved_targets_are_not_interpolated(self):
        series = {'times': np.array([0, 900]), 'level': np.array([5, np.nan])}
        values, _ = sample(series, np.array([900, 6300]))
        self.assertEqual(values[0], 5)
        self.assertTrue(np.isnan(values[1]))
        exact, _ = sample(series, np.array([900]), max_age=0)
        self.assertTrue(np.isnan(exact[0]))
        X, _ = features(self.series(), np.array([12 * 3600]), (6300, 0))
        self.assertTrue(np.isnan(X[0, 0]))

    def test_delayed_anchor_uses_actual_time_and_own_gauge(self):
        series = self.series()
        series[STATIONS[1]]['level'] += 10
        X, anchor = features(series, np.array([12 * 3600]), (5400, 0))
        self.assertAlmostEqual(anchor[0], 5.05)
        self.assertAlmostEqual(X[0, 1], 1.5)
        self.assertAlmostEqual(X[0, 2], .1)
        self.assertAlmostEqual(X[0, 7], 15.2)

    def test_parser_rejects_other_station_and_bad_quality(self):
        xml = '<root><DadosHidrometereologicos><CodEstacao>86720000</CodEstacao><DataHora>2026-09-21T10:00:00</DataHora><NivelFinal>710</NivelFinal><CQ_NivelFinal>Dado suspeito</CQ_NivelFinal></DadosHidrometereologicos></root>'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'ana.xml'
            path.write_text(xml)
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                read_levels(path, '86510000', 2e9)
            self.assertTrue(np.isnan(read_levels(path, '86720000', 2e9)['level'][0]))
            path.write_text(xml.replace('Dado suspeito', 'Dado aprovado'))
            self.assertEqual(read_levels(path, '86720000', 2e9)['level'][0], 7.1)

    def test_inference_rejects_stale_input_before_loading_models(self):
        with patch('hydro_encantado.joblib.load') as load:
            with self.assertRaisesRegex(ValueError, 'stale'):
                predict(self.series(), datetime.now(TZ))
            load.assert_not_called()

    def test_santa_tereza_features_use_city_as_anchor_and_own_upstream(self):
        codes = MODEL_CONFIGS['santa-tereza']['codes']
        series = dict(zip(codes, self.series().values()))
        series[codes[1]]['level'] += 3
        X, anchor = features(series, np.array([12 * 3600]), stations=codes)
        self.assertAlmostEqual(anchor[0], 5.2)
        self.assertAlmostEqual(X[0, 7], 8.2)
        before = X.copy()
        for s in series.values():
            s['level'][s['times'] > 12 * 3600] = 99
        after, _ = features(series, np.array([12 * 3600]), stations=codes)
        np.testing.assert_array_equal(before, after)

    def test_santa_tereza_rejects_encantado_artifacts(self):
        with self.assertRaisesRegex(ValueError, 'specification'):
            predict({}, datetime.now(TZ), model_dir=ROOT / 'model-artifacts' / VERSION, station='santa-tereza')

    def test_packaged_models_pass_chronological_gate_and_hashes(self):
        import hashlib
        for config in MODEL_CONFIGS.values():
            with self.subTest(station=config['label']):
                folder = ROOT / 'model-artifacts' / config['version']
                spec = json.loads((folder / 'model.json').read_text())
                self.assertTrue(spec['validationPassed'])
                for row in spec['metrics']:
                    for phase in ['validation', 'test']:
                        self.assertLess(row[phase]['mae_m'], row[phase]['persistence_mae_m'])
                for name, digest in spec['artifacts'].items():
                    self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
