"""Rain/network failures cannot become dependencies of hydrometric inference."""
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hydro_hourly_collect import collection_jobs, collect, TZ


class CollectionScopeTests(unittest.TestCase):
    def test_hydrometry_uses_only_its_seven_sources_without_rain_configuration(self):
        now = datetime(2026, 9, 23, 10, tzinfo=TZ)
        with patch.object(Path, 'read_text', side_effect=AssertionError('Unexpected rain dependency')):
            jobs = collection_jobs(now, hydrometric_only=True)
        expected = {f'ana-{code}-fresh.xml' for code in ('86472000', '86472600', '86500000', '86510000')} | {
            'ceran-julho-fresh.html', 'ceran-monte-fresh.html', 'ceran-castro-fresh.html'}
        self.assertEqual({job[0] for job in jobs}, expected)
        self.assertEqual(len(jobs), 7)

    def test_hydrometric_collector_keeps_failed_required_receipts_without_other_requests(self):
        now = datetime(2026, 9, 23, 10, tzinfo=TZ)
        with tempfile.TemporaryDirectory() as folder:
            with patch('hydro_hourly_collect.urllib.request.urlopen', side_effect=OSError('test provider down')) as network:
                manifest = collect(Path(folder), now, hydrometric_only=True)
            self.assertEqual(len(manifest), 7)
            self.assertTrue(all('error' in row and 'collected_at' in row for row in manifest))
            self.assertEqual(network.call_count, 14)  # one bounded retry per required source
            self.assertTrue(all('open-meteo' not in call.args[0].full_url and 'sigmameteorologia' not in call.args[0].full_url for call in network.call_args_list))


if __name__ == '__main__':
    unittest.main()
