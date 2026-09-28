"""As-of, QC, coverage and missing-data tests for optional rainfall evidence."""
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from hydro_hourly_collect import TZ, collect, collection_jobs
import hydro_rain_context as rain


REFERENCE = datetime(2026, 9, 28, 15, tzinfo=TZ)
ISSUED = REFERENCE + timedelta(minutes=15)
GROUPS = ('Baixo Antas', 'Carreiro', 'Prata-Turvo', 'Alto Antas', 'Tainhas')


def ana_xml(code, *, suspect=False, after_reference_mm=80):
    rows = []
    for h in range(-24, 2):
        at = REFERENCE + timedelta(hours=h)
        amount = after_reference_mm if h == 1 else 2
        quality = 'Dado suspeito' if suspect and h == 0 else 'Dado aprovado'
        rows.append(f'<DadosHidrometereologicos><CodEstacao>{code}</CodEstacao>'
                    f'<DataHora>{at:%Y-%m-%dT%H:%M:%S}</DataHora>'
                    f'<ChuvaFinal>{amount}</ChuvaFinal><CQ_ChuvaFinal>{quality}</CQ_ChuvaFinal>'
                    '</DadosHidrometereologicos>')
    return ('<DataTable>' + ''.join(rows) + '</DataTable>').encode()


def weather_json(*, missing_at=None):
    rows = []
    for _ in GROUPS:
        hours = [REFERENCE + timedelta(hours=h) for h in range(1, 8)]
        rows.append({'latitude': -29., 'longitude': -51., 'utc_offset_seconds': -10800,
                     'hourly_units': {'precipitation': 'mm'},
                     'hourly': {'time': [at.strftime('%Y-%m-%dT%H:%M') for at in hours],
                                'precipitation': [None if at == missing_at else 3. for at in hours]}})
    return json.dumps(rows).encode()


class RainContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        (self.out / 'raw').mkdir()
        self.weights = self.out / 'weights.json'
        self.query = self.out / 'query.json'
        self.weights.write_text(json.dumps([
            {'group': group, 'area_km2': 100., 'weights': {'111': .6, '222': .4}}
            for group in GROUPS]))
        self.query.write_text(json.dumps({'groups': GROUPS,
            'url': 'https://api.open-meteo.com/v1/forecast?latitude=-29,-29,-29,-29,-29&longitude=-51,-51,-51,-51,-51'}))
        self.patches = [patch.object(rain, 'RAIN_WEIGHTS', self.weights),
                        patch.object(rain, 'RAIN_QUERY', self.query)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.receipts = []

    def add(self, name, body, *, collected=None, requested=None):
        (self.out / 'raw' / name).write_bytes(body)
        self.receipts.append({'file': name, 'source': 'ANA' if name.startswith('ana') else 'Open-Meteo',
                              'sha256': hashlib.sha256(body).hexdigest(),
                              'requested_at': (requested or REFERENCE).isoformat(),
                              'collected_at': (collected or ISSUED - timedelta(minutes=1)).isoformat(),
                              'issued_at': None})

    def finish(self):
        (self.out / 'collection-manifest.json').write_text(json.dumps(self.receipts))
        return rain.normalize_rain_context(self.out, REFERENCE, ISSUED)

    def test_observed_rain_excludes_post_reference_and_forecast_remains_shadow(self):
        for code in ('111', '222'):
            self.add(f'ana-{code}-fresh.xml', ana_xml(code))
        for model in rain.MODELS:
            self.add(f'weather-{model}.json', weather_json())
        result = self.finish()
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['shadowOnly'])
        self.assertFalse(result['providerRunTimeVerified'])
        for region in result['regions'].values():
            self.assertEqual(region['windows']['6']['mm'], 12)
            self.assertEqual(region['windows']['6']['spatialCoverage'], 1)
        for model in result['forecastModels'].values():
            self.assertEqual(model['points'][GROUPS[0]]['futureCumulativeMmByLead'], [3, 6, 9, 12, 15, 18])

    def test_missing_and_suspect_gauges_do_not_become_dry(self):
        self.add('ana-111-fresh.xml', ana_xml('111', suspect=True))
        result = self.finish()
        region = result['regions'][GROUPS[0]]
        self.assertIsNone(region['windows']['6']['mm'])
        self.assertEqual(region['windows']['6']['spatialCoverage'], 0)
        self.assertEqual(result['status'], 'unavailable')

    def test_receipt_after_issuance_is_rejected(self):
        self.add('ana-111-fresh.xml', ana_xml('111'), collected=ISSUED + timedelta(minutes=1))
        result = self.finish()
        self.assertIsNone(result['regions'][GROUPS[0]]['windows']['1']['mm'])
        self.assertTrue(any('after issuance' in issue['reason'] for issue in result['issues']))

    def test_weather_missing_one_hour_does_not_impute_future(self):
        for code in ('111', '222'):
            self.add(f'ana-{code}-fresh.xml', ana_xml(code))
        self.add('weather-gfs_seamless.json', weather_json(missing_at=REFERENCE + timedelta(hours=3)))
        result = self.finish()
        totals = result['forecastModels']['gfs_seamless']['points'][GROUPS[0]]['futureCumulativeMmByLead']
        self.assertEqual(totals[:2], [3, 6])
        self.assertEqual(totals[2:], [None] * 4)
        self.assertFalse(result['forecastSixHourCoverageReady'])

    def test_weather_labels_reference_leads_that_have_elapsed_at_issue(self):
        self.add('weather-gfs_seamless.json', weather_json(),
                 collected=REFERENCE + timedelta(minutes=69))
        (self.out / 'collection-manifest.json').write_text(json.dumps(self.receipts))
        issued = REFERENCE + timedelta(minutes=70)
        result = rain.normalize_rain_context(self.out, REFERENCE, issued)
        point = result['forecastModels']['gfs_seamless']['points'][GROUPS[0]]
        self.assertEqual(point['targetIsFutureAtIssue'], [False, True, True, True, True, True])

    def test_weather_point_must_match_frozen_region_coordinate(self):
        body = json.loads(weather_json())
        body[0]['latitude'] = -25
        self.add('weather-gfs_seamless.json', json.dumps(body).encode())
        result = self.finish()
        self.assertEqual(result['forecastModels']['gfs_seamless']['status'], 'unavailable')
        self.assertTrue(any('does not match' in issue['reason'] for issue in result['issues']))

    def test_tampered_body_is_rejected(self):
        self.add('ana-111-fresh.xml', ana_xml('111'))
        (self.out / 'raw/ana-111-fresh.xml').write_text('changed')
        result = self.finish()
        self.assertTrue(any('hash mismatch' in issue['reason'] for issue in result['issues']))

    def test_collection_jobs_add_optional_sources_only_when_requested(self):
        basic = collection_jobs(REFERENCE, hydrometric_only=True)
        expanded = collection_jobs(REFERENCE, hydrometric_only=True, rain_context=True)
        self.assertEqual(len(basic), 7)
        self.assertEqual(len(expanded), 33)
        self.assertEqual({name for name, _, _ in expanded[:7]}, {name for name, _, _ in basic})

    def test_invalid_rain_configuration_does_not_abort_hydrometric_collection(self):
        class Response:
            status = 200
            headers = {'Date': 'Mon, 28 Sep 2026 18:00:00 GMT'}
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return b'body'
        with patch('hydro_hourly_collect.RAIN_WEIGHTS', self.out / 'missing.json'), \
             patch('hydro_hourly_collect.urllib.request.urlopen', return_value=Response()):
            manifest = collect(self.out / 'collection', REFERENCE,
                               hydrometric_only=True, rain_context=True)
        self.assertEqual(sum('sha256' in row for row in manifest), 7)
        self.assertEqual(len(manifest), 8)
        self.assertEqual(manifest[0]['file'], 'rain-context-configuration')

    def test_optional_deadline_keeps_required_receipts_and_no_late_writes(self):
        class Response:
            status = 200
            headers = {'Date': 'Mon, 28 Sep 2026 18:00:00 GMT'}
            def __init__(self, optional): self.optional = optional
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self):
                if self.optional: time.sleep(.06)
                return b'body'
        # The frozen production weight file adds 23 optional ANA sources. All
        # their mocked requests pause; the deadline must return immediately.
        with patch('hydro_hourly_collect.RAIN_CONTEXT_DEADLINE_SECONDS', 0), \
             patch('hydro_hourly_collect.urllib.request.urlopen', side_effect=lambda request, timeout: Response(
                 timeout == 6)):
            manifest = collect(self.out / 'deadline', REFERENCE,
                               hydrometric_only=True, rain_context=True)
        self.assertEqual(len(manifest), 33)
        self.assertEqual(sum('sha256' in row for row in manifest), 7)
        self.assertEqual(sum('error' in row for row in manifest), 26)
        time.sleep(.15)
        self.assertEqual(len(list((self.out / 'deadline/raw').iterdir())), 7)


if __name__ == '__main__':
    unittest.main()
