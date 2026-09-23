import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import numpy as np
from hydro_history import TZ, sha
from hydro_input_readiness import evaluate, require_features, InputsNotReady, GROUPS, LEVELS, PLANTS
import hydro_hourly_forecast as hourly
import hydro_site_projection as site
import hydro_prospective_ledger as ledger
from hydro_feature_contract import ContractError, feature_definitions, validate_snapshot


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        (self.out / 'raw').mkdir()
        self.ref = datetime.now(TZ).replace(minute=0, second=0, microsecond=0)
        self.weights = self.out / 'weights.json'
        self.weights.write_text(json.dumps([{'group': g, 'weights': {LEVELS[0]: .6, LEVELS[1]: .4}} for g in GROUPS]))
        for code in LEVELS:
            self.ana(code)
        for plant in PLANTS:
            cells = [self.ref.strftime('%d/%m/%Y %H:%M:%S'), '0', '0', '100', '0', '0', '0', '100']
            (self.out / 'raw' / f'ceran-{plant}-fresh.html').write_text('<tr>' + ''.join(f'<td>{v}</td>' for v in cells) + '</tr>')
        for model in hourly.MODELS:
            (self.out / 'raw' / f'weather-{model}.json').write_text('[]')
        self.manifest()

    def ana(self, code, shift=0, qc='Dado aprovado', rain='0', level='1000', partial=False):
        rows = []
        for minutes in ([-15, 0] if partial else [-60, -45, -30, -15, 0]):
            t = self.ref + timedelta(minutes=minutes + shift)
            rows.append(f'<DadosHidrometereologicos><CodEstacao>{code}</CodEstacao><DataHora>{t.isoformat()}</DataHora><NivelFinal>{level}</NivelFinal><CQ_NivelFinal>{qc}</CQ_NivelFinal><ChuvaFinal>{rain}</ChuvaFinal><CQ_ChuvaFinal>{qc}</CQ_ChuvaFinal></DadosHidrometereologicos>')
        (self.out / 'raw' / f'ana-{code}-fresh.xml').write_text('<root>' + ''.join(rows) + '</root>')

    def manifest(self):
        (self.out / 'collection-manifest.json').write_text(json.dumps([
            {'file': p.name, 'sha256': sha(p), 'collected_at': datetime.now(TZ).isoformat(),
             'source': 'ANA' if p.suffix == '.xml' else 'CERAN' if p.suffix == '.html' else 'Open-Meteo'}
            for p in (self.out / 'raw').iterdir()]))

    def check(self):
        self.manifest()
        return evaluate(self.out, self.ref, self.weights)

    def test_complete_same_hour_zero_rain_is_ready(self):
        self.assertEqual(self.check()['status'], 'ready')

    def test_fresh_download_of_old_level_cannot_pass(self):
        self.ana(LEVELS[0], shift=-15)
        report = self.check()
        self.assertEqual(report['status'], 'waiting_for_data')
        self.assertTrue(any('river level missing' in m for m in report['missing']))

    def test_rejected_or_absent_qc_cannot_pass(self):
        for qc in ['Dado rejeitado', '']:
            self.ana(LEVELS[0], qc=qc)
            self.assertEqual(self.check()['status'], 'waiting_for_data')

    def test_missing_rain_is_not_dry_weather(self):
        self.ana(LEVELS[0], rain='')
        self.assertEqual(self.check()['rainCoverage']['Tainhas'], .4)

    def test_partial_hour_does_not_count_as_complete_station(self):
        self.ana(LEVELS[0], partial=True)
        self.assertEqual(self.check()['status'], 'waiting_for_data')

    def test_missing_minor_rain_station_allowed_in_all_five_regions(self):
        self.ana(LEVELS[1], rain='')
        self.assertEqual(self.check()['status'], 'ready')
        self.assertEqual(self.check()['rainCoverage']['Tainhas'], .6)

    def optional_rain_weights(self, missing_weight=.4):
        self.weights.write_text(json.dumps([{'group': group, 'weights': {
            LEVELS[0]: 1-missing_weight, '99999999': missing_weight}} for group in GROUPS]))

    def test_missing_optional_rain_download_uses_regional_coverage(self):
        self.optional_rain_weights()
        report = self.check()
        self.assertEqual(report['status'], 'ready')
        self.assertEqual(report['rainCoverage']['Tainhas'], .6)
        self.assertIn('ana-99999999-fresh.xml', report['unavailableRainSources'])
        self.assertEqual(report['missing'], [])

    def test_failed_optional_rain_source_does_not_inflate_coverage(self):
        self.optional_rain_weights(missing_weight=.6)
        self.manifest()
        path = self.out / 'collection-manifest.json'
        items = json.loads(path.read_text())
        items.append({'file': 'ana-99999999-fresh.xml', 'source': 'ANA',
                      'error': 'transport failed', 'collected_at': datetime.now(TZ).isoformat()})
        path.write_text(json.dumps(items))
        report = evaluate(self.out, self.ref, self.weights)
        self.assertEqual(report['status'], 'waiting_for_data')
        self.assertEqual(report['rainCoverage']['Tainhas'], .4)
        self.assertEqual(len(report['missing']), 5)
        self.assertTrue(all('coverage' in reason for reason in report['missing']))

    def test_optional_rain_tampering_cannot_be_hidden_as_transport_failure(self):
        self.optional_rain_weights()
        self.ana('99999999')
        self.manifest()
        path = self.out / 'collection-manifest.json'
        items = json.loads(path.read_text())
        next(item for item in items if item['file'] == 'ana-99999999-fresh.xml')['error'] = 'transport failed'
        path.write_text(json.dumps(items))
        (self.out / 'raw/ana-99999999-fresh.xml').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            evaluate(self.out, self.ref, self.weights)

    def test_missing_optional_rain_masks_only_feature_view_not_saved_history(self):
        import hydro_latency_forecast as latency
        times = np.arange(self.ref.timestamp()-7200, self.ref.timestamp()+1, 900)
        np.savez(self.out/'telemetria.npz', times=times)
        history = self.out/'cached-history';history.mkdir()
        for plant in PLANTS:
            np.savez(history/f'ceran-{plant}.npz', times=times,
                     Q=np.full(len(times),100.), I=np.full(len(times),100.))
        series = {code:{'times':times, 'level':np.full(len(times),10.),
                        'flow':np.full(len(times),100.), 'rain':np.full(len(times),rain),
                        'counter':np.zeros(len(times))}
                  for code,rain in [(LEVELS[0],0.),('99999999',20.)]}
        np.savez(history/'ana-99999999.npz', **series['99999999'])
        original = (history/'ana-99999999.npz').read_bytes()
        report = {'status':'ready','referenceAt':self.ref.isoformat(),
                  'unavailableRainSources':{'ana-99999999-fresh.xml':'source unavailable'}}
        (self.out/'input-readiness.json').write_text(json.dumps(report))
        for available_weight in [.6,.4]:
            (self.out/'chuva-pesos.json').write_text(json.dumps([
                {'group':group,'weights':{LEVELS[0]:available_weight,'99999999':1-available_weight}}
                for group in GROUPS]))
            with patch.object(latency,'OUT',self.out), patch.object(latency,'PREV',self.out), \
                 patch.object(latency,'merged',side_effect=lambda code:series[code]), \
                 patch.dict('os.environ',{'HYDRO_REQUIRE_COMPLETE':'1','HYDRO_ORIGIN':self.ref.isoformat(),
                                         'HYDRO_HISTORY_DIR':str(history)}):
                _,_,features,_ = latency.prepare_current()
            self.assertAlmostEqual(features['Tainhas:C1'][-1],available_weight)
            if available_weight>=.5:
                self.assertEqual(features['Tainhas:P1'][-1],0.)
            else:
                self.assertTrue(np.isnan(features['Tainhas:P1'][-1]))
                with self.assertRaises(InputsNotReady):
                    require_features(np.array([features['Tainhas:P1'][-1]]))
            self.assertEqual((history/'ana-99999999.npz').read_bytes(),original)
            np.testing.assert_array_equal(series['99999999']['rain'],np.full(len(times),20.))

    def test_a_single_region_below_threshold_blocks(self):
        groups = json.loads(self.weights.read_text())
        groups[-1]['weights'] = {LEVELS[1]: 1.}
        self.weights.write_text(json.dumps(groups))
        self.ana(LEVELS[1], rain='')
        self.assertEqual(self.check()['missing'], ['Tainhas: same-hour rain coverage 0.0% below 50%'])

    def test_missing_inflow_or_outflow_blocks(self):
        for column in [3, 7]:
            p = self.out / 'raw/ceran-julho-fresh.html'
            cells = [self.ref.strftime('%d/%m/%Y %H:%M:%S'), '0', '0', '100', '0', '0', '0', '100']
            cells[column] = ''
            p.write_text('<tr>' + ''.join(f'<td>{v}</td>' for v in cells) + '</tr>')
            self.assertEqual(self.check()['status'], 'waiting_for_data')

    def test_conflicting_duplicate_blocks(self):
        p = self.out / 'raw' / f'ana-{LEVELS[0]}-fresh.xml'
        first = p.read_text()
        p.write_text(first.replace('</root>', '') + first.replace('<NivelFinal>1000</NivelFinal>', '<NivelFinal>2000</NivelFinal>').replace('<root>', ''))
        self.assertTrue(any('Conflicting ANA duplicate' in m for m in self.check()['missing']))

    def test_future_reference_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(self.out, self.ref + timedelta(hours=1), self.weights)

    def test_finite_feature_gate_does_not_impute(self):
        for bad in [np.nan, np.inf]:
            with self.assertRaises(InputsNotReady):
                require_features(np.array([0., bad, 1.]))
        require_features(np.zeros(180))

    def test_waiting_cycle_is_not_completed(self):
        root = self.out / 'ledger'
        report = {'status': 'waiting_for_data', 'missing': ['rain']}
        with patch('sys.argv', ['run', '--ledger', str(root)]), patch.object(hourly, 'execute', side_effect=InputsNotReady(report)), patch.object(ledger, 'report') as scoring:
            hourly.run()
            scoring.assert_not_called()
        self.assertEqual([r['kind'] for r in ledger.read_records(root)], ['cycle_started', 'cycle_waiting_for_data'])

    def test_site_wait_preserves_output_and_never_builds_or_calculates(self):
        state = self.out / 'state'
        state.mkdir()
        original = json.dumps({'referenceAt': (self.ref-timedelta(hours=1)).isoformat(), 'sentinel': 'last valid forecast'})
        (state / 'result.json').write_text(original)
        self.ana(LEVELS[0], shift=-15)
        self.manifest()
        with patch('sys.argv', ['run', '--state', str(state), '--source', str(self.out), '--attempt-id', 'test']), patch.object(site, 'PREV', self.out), patch.dict('os.environ', {'OBJECT_STORAGE_URL': ''}), patch.object(site.hydro_history, 'build') as build, patch.object(site, 'calculate_model') as calculate:
            (self.out / 'chuva-pesos.json').write_text(self.weights.read_text())
            site.main()
            build.assert_not_called()
            calculate.assert_not_called()
        self.assertEqual((state / 'result.json').read_text(), original)
        self.assertEqual(json.loads((state / 'refresh-status.json').read_text())['status'], 'waiting_for_data')

    def test_missing_derived_feature_blocks_both_model_entrypoints(self):
        import hydro_latency_forecast as latency
        t = np.array([self.ref.timestamp()])
        X = np.zeros((1, 120)); X[0, 40] = np.nan
        ages = [{'source': '86510000', 'delay_minutes': 0, 'value': 10.}]
        with patch.object(latency, 'prepare_current', return_value=(t, {}, {}, ages)), patch.object(latency, 'telemetry_features', return_value=(t, X, np.array([10.]), np.array([10.]), np.array([0]), X)), patch.object(site, 'require_ready'), patch.object(hourly, 'require_ready'), patch.object(site, 'current_nwp_features', return_value=np.zeros(60)), patch.object(hourly, 'weather_features', return_value=np.zeros((1, 60))), patch.object(site.joblib, 'load') as load, patch.object(hourly.HistGradientBoostingRegressor, 'fit') as fit:
            with self.assertRaises(InputsNotReady):
                site.calculate_model(self.out, self.ref)
            # Research training must also fail closed on the legacy NWP
            # contract, before any estimator sees these incomplete features.
            with self.assertRaises(ContractError):
                hourly.calculate(self.out, self.out / 'ledger', self.ref, [])
            load.assert_not_called()
            fit.assert_not_called()

    def test_publication_retry_reuses_complete_saved_issue_without_calculation(self):
        state = self.out / 'state'; state.mkdir()
        prior = {'referenceAt': self.ref.isoformat(), 'generatedAt': datetime.now(TZ).isoformat(), 'modelVersion': site.MODEL_VERSION, 'modelSha256':site.MODEL_SHA256, 'archiveReceiptKey': 'projection/receipts/first-issue.json',
                 'models':[{'id':site.MODEL_ID,'points':[{'timestamp':(self.ref+timedelta(hours=hour)).isoformat(),'level':10.} for hour in range(1,7)]}]}
        (state / 'result.json').write_text(json.dumps(prior))
        with patch('sys.argv', ['run', '--state', str(state), '--attempt-id', 'retry']), patch.object(site, 'collect') as collect, patch.object(site, 'calculate_model') as calculate:
            site.main()
            collect.assert_not_called()
            calculate.assert_not_called()
        status = json.loads((state / 'refresh-status.json').read_text())
        self.assertEqual(status['generatedAt'], prior['generatedAt'])
        self.assertEqual(status['attemptId'], 'retry')
        self.assertEqual(status['archiveReceiptKey'], prior['archiveReceiptKey'])

    def test_real_feature_snapshot_and_shadow_share_received_inputs(self):
        received = self.ref + timedelta(minutes=10)
        generated = self.ref + timedelta(minutes=20)
        manifest = json.loads((self.out / 'collection-manifest.json').read_text())
        for row in manifest:
            row['collected_at'] = received.isoformat()
        (self.out / 'collection-manifest.json').write_text(json.dumps(manifest))
        readiness = evaluate(self.out, self.ref, self.weights, now=generated)
        self.assertEqual(readiness['status'], 'ready')
        (self.out / 'input-readiness.json').write_text(json.dumps(readiness))
        # This is a real valid 180-column contract fixture, including transformed
        # flows and measured rain coverage; no snapshot/shadow helper is mocked.
        features = [max(0., field['minimum'] or 0.) for field in feature_definitions()]
        for index, station in enumerate(LEVELS):
            features[index * 6] = readiness['levels'][station]
        for index, plant in enumerate(PLANTS):
            q, inflow = readiness['flows'][plant]
            features[24 + index * 7:27 + index * 7] = [(q / 1000) ** .6, q / 1000, inflow / 1000]
        (self.out / 'current-features.json').write_text(json.dumps(features))
        metadata = {'trainingCutoff': '2026-09-21T00:00:00-03:00',
                    'model': {'id': 'fixture-frozen', 'artifacts': {'fixture.joblib': 'a' * 64}},
                    'sourceAges': [{'source': '86510000', 'delay_minutes': 0}],
                    'runtimeManifest': {'fixture.py': 'b' * 64},
                    'trainingFeatureContract': 'legacy-mixed-nwp-unverified'}
        (self.out / 'model-metadata.json').write_text(json.dumps(metadata))
        points = [{'timestamp': (self.ref + timedelta(hours=hour)).isoformat(), 'level': 10.2}
                  for hour in range(1, 7)]
        original = json.dumps(points, sort_keys=True)
        site.record_features_and_shadow(self.out, self.ref, generated.isoformat(),
                                        {'value': 10.}, points)
        snapshot = json.loads((self.out / 'feature-snapshot.json').read_text())
        shadow = json.loads((self.out / 'short-term-shadow.json').read_text())
        self.assertEqual(validate_snapshot(snapshot), [])
        self.assertEqual(snapshot['features'], features)
        self.assertEqual(snapshot['model']['trainingFeatureContract'], 'legacy-mixed-nwp-unverified')
        self.assertEqual(snapshot['model']['collectionManifestSha256'], sha(self.out / 'collection-manifest.json'))
        self.assertEqual(shadow['status'], 'shadow_generated')
        self.assertFalse(shadow['publishable'])
        self.assertFalse(shadow['goalEvidenceEligible'])
        self.assertEqual(shadow['inputEvidence']['anchor']['received_at'], received.isoformat())
        self.assertEqual(shadow['inputEvidence']['received_history'][0]['timestamp'],
                         (self.ref - timedelta(hours=1)).isoformat())
        self.assertEqual(shadow['points'][-1]['shadowLevel'], points[-1]['level'])
        self.assertEqual(json.dumps(points, sort_keys=True), original)
        self.assertFalse((self.out / 'forecast.json').exists())

if __name__ == '__main__':
    unittest.main()
