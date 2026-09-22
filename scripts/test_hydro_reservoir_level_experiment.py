import unittest
import numpy as np
from hydro_reservoir_level_experiment import prepare_levels, epoch, PLANTS


def rows(stamps):
    return [{'id_reservatorio': code, 'din_instante': at, 'val_nivelmontante': value,
             'val_niveljusante': str(float(value)-5) if value else ''}
            for code in PLANTS.values() for at, value in stamps]


class ReservoirLevelsTest(unittest.TestCase):
    def test_delay_and_exact_age_limit(self):
        raw = rows([('2026-01-01T00:30:00-03:00', '100')])
        t = np.arange(epoch('2026-01-01T01:00:00-03:00'), epoch('2026-01-01T05:00:00-03:00'), 3600)
        x, _, _ = prepare_levels(raw, t)
        np.testing.assert_allclose(x[:, 0], [np.nan, 100, 100, np.nan], equal_nan=True)

    def test_missing_newest_is_not_bypassed_and_future_is_not_used(self):
        raw = rows([('2026-01-01T00:00:00-03:00', '100'), ('2026-01-01T01:00:00-03:00', ''), ('2026-01-01T03:00:00-03:00', '200')])
        t = np.array([epoch('2026-01-01T02:00:00-03:00')])
        x, _, _ = prepare_levels(raw, t)
        self.assertTrue(np.isnan(x).all())

    def test_midnight_is_not_shifted_and_duplicates_rejected(self):
        raw = rows([('2026-01-01T23:59:00-03:00', '100')])
        t = np.arange(epoch('2026-01-02T00:00:00-03:00'), epoch('2026-01-02T02:00:00-03:00'), 3600)
        x, _, trace = prepare_levels(raw, t)
        np.testing.assert_allclose(x[:, 0], [np.nan, 100], equal_nan=True)
        self.assertTrue(trace[1]['source_time'].endswith('23:59:00-03:00'))
        with self.assertRaises(ValueError):
            prepare_levels(raw+[raw[0]], t)


if __name__ == '__main__':
    unittest.main()
