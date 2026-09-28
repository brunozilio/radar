"""Operational receipt, clock and baseline isolation checks; local fixtures only."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from hydro_history import TZ, sha
import hydro_propagation_live as live


class PropagationLiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / 'attempt'
        (self.out / 'raw').mkdir(parents=True)
        self.ref = datetime(2026, 9, 23, 10, tzinfo=TZ)
        self.now = self.ref + timedelta(minutes=15)
        for code in live.LEVELS:
            body = '<root>' + ''.join(
                f'<DadosHidrometereologicos><CodEstacao>{code}</CodEstacao>'
                f'<DataHora>{(self.ref-timedelta(hours=h)).isoformat()}</DataHora>'
                '<NivelFinal>1200</NivelFinal><CQ_NivelFinal>Dado aprovado</CQ_NivelFinal>'
                '</DadosHidrometereologicos>' for h in range(35)) + '</root>'
            (self.out / 'raw' / f'ana-{code}-fresh.xml').write_text(body)
        for plant in live.PLANTS:
            rows = []
            for h in range(35):
                cells = [(self.ref-timedelta(hours=h)).strftime('%d/%m/%Y %H:%M:%S'), '0', '0', '100', '0', '0', '0', '100']
                rows.append('<tr>' + ''.join(f'<td>{v}</td>' for v in cells) + '</tr>')
            (self.out / 'raw' / f'ceran-{plant}-fresh.html').write_text(''.join(rows))
        self.manifest = [dict(file=p.name, collected_at=(self.now-timedelta(minutes=1)).isoformat(), sha256=sha(p))
                         for p in (self.out / 'raw').iterdir()]
        self.write_manifest()
        model = self.root / live.MODEL_PATH
        model.parent.mkdir(parents=True)
        model.write_text('{}')

    def write_manifest(self):
        (self.out / 'collection-manifest.json').write_text(json.dumps(self.manifest))

    def prediction(self, model, times, data, reference_at, issued_at):
        reference = datetime.fromisoformat(reference_at)
        issued = datetime.fromisoformat(issued_at)
        return dict(modelVersion='fixture', contract='fixture', uncertainty='Not a safety bound',
                    extrapolatedFeatures=['flow outside training range'], observation=dict(timestamp=reference_at, level=12),
                    points=[dict(timestamp=(reference+timedelta(hours=h)).isoformat(), level=12, nominalLeadHours=h)
                            for h in range(1, 7) if reference+timedelta(hours=h) > issued])

    def test_rain_and_nwp_are_not_required_and_input_order_is_exact(self):
        times, data, sources = live.load_inputs(self.out, self.ref, self.now)
        self.assertEqual(len(sources), 7)
        self.assertEqual(data['86510000:H'][-1], 12)
        self.assertEqual(data['julho:Q'][-1], 100)
        self.assertTrue(np.isnan(data['julho:Q'][0]))
        with patch.object(live, 'predict', side_effect=self.prediction):
            result = live.run_shadow(self.out, self.root, self.ref, now=self.now)
        self.assertEqual(result['status'], 'calculated')
        self.assertFalse(result['publishable'])
        self.assertEqual(result['extrapolatedFeatures'], ['flow outside training range'])
        self.assertEqual(result['uncertainty'], 'Not a safety bound')
        self.assertEqual(len(result['points']), 6)
        self.assertTrue(all(p['realLeadHours'] > 0 for p in result['points']))
        self.assertFalse((self.out / 'forecast.json').exists())
        self.assertEqual(json.loads((self.out / 'local-nowcast-shadow.json').read_text())['status'], 'unavailable')

    def test_local_nowcast_uses_only_approved_received_readings_and_caps_change(self):
        path = self.out / 'raw' / 'ana-86510000-fresh.xml'
        newer = self.ref + timedelta(minutes=10)
        extra = (f'<DadosHidrometereologicos><CodEstacao>86510000</CodEstacao>'
                 f'<DataHora>{newer.isoformat()}</DataHora><NivelFinal>1290</NivelFinal>'
                 '<CQ_NivelFinal>Dado aprovado</CQ_NivelFinal></DadosHidrometereologicos>')
        future = (f'<DadosHidrometereologicos><CodEstacao>86510000</CodEstacao>'
                  f'<DataHora>{(self.now+timedelta(minutes=15)).isoformat()}</DataHora>'
                  '<NivelFinal>2000</NivelFinal><CQ_NivelFinal>Dado aprovado</CQ_NivelFinal>'
                  '</DadosHidrometereologicos>')
        path.write_text(path.read_text().replace('</root>', extra+future+'</root>'))
        next(row for row in self.manifest if row['file'] == path.name)['sha256'] = sha(path)
        self.write_manifest()
        with patch.object(live, 'predict', side_effect=self.prediction):
            original = live.run_shadow(self.out, self.root, self.ref, now=self.now)
        candidate = json.loads((self.out / 'local-nowcast-shadow.json').read_text())
        self.assertEqual(candidate['status'], 'calculated')
        self.assertFalse(candidate['publishable'])
        self.assertEqual(candidate['observation']['timestamp'], newer.isoformat())
        self.assertEqual(candidate['correctionMetres'], .5)
        self.assertEqual(candidate['points'][0]['candidateLevel'], 12.5)
        self.assertEqual(original['points'][0]['level'], 12)
        path.write_text(path.read_text().replace(extra, extra.replace('Dado aprovado', 'Dado bruto')))
        next(row for row in self.manifest if row['file'] == path.name)['sha256'] = sha(path)
        self.write_manifest()
        with patch.object(live, 'predict', side_effect=self.prediction):
            live.run_shadow(self.out, self.root, self.ref, now=self.now)
        self.assertEqual(json.loads((self.out / 'local-nowcast-shadow.json').read_text())['status'], 'unavailable')

    def test_stale_future_and_failed_receipts_never_run_inference(self):
        for age in (-1, 3601):
            self.manifest[0]['collected_at'] = (self.now-timedelta(seconds=age)).isoformat()
            self.write_manifest()
            with patch.object(live, 'predict') as prediction:
                result = live.run_shadow(self.out, self.root, self.ref, now=self.now)
            self.assertEqual(result['status'], 'unavailable')
            prediction.assert_not_called()
        self.manifest[0]['error'] = 'provider unavailable'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'source unavailable'):
            live.load_inputs(self.out, self.ref, self.now)

    def test_tampered_body_or_runtime_model_never_runs(self):
        path = self.out / 'raw' / self.manifest[0]['file']
        path.write_text(path.read_text() + '<unexpected/>')
        with patch.object(live, 'predict') as prediction:
            result = live.run_shadow(self.out, self.root, self.ref, now=self.now)
        self.assertIn('checksum mismatch', result['reason'])
        prediction.assert_not_called()
        (self.root / 'manifest.json').write_text(json.dumps({str(live.MODEL_PATH): '0'*64}))
        result = live.run_shadow(self.out, self.root, self.ref, now=self.now)
        self.assertIn('model runtime checksum mismatch', result['reason'])

    def test_selected_older_hour_preserves_reference_and_nominal_targets(self):
        def delayed(model, times, data, reference_at, issued_at):
            if reference_at == self.ref.isoformat():
                raise ValueError('Missing exact required level')
            return self.prediction(model, times, data, reference_at, issued_at)
        with patch.object(live, 'predict', side_effect=delayed):
            result = live.run_shadow(self.out, self.root, self.ref, now=self.now)
        self.assertEqual(result['referenceAt'], (self.ref-timedelta(hours=1)).isoformat())
        self.assertEqual(result['points'][0]['nominalLeadHours'], 2)
        self.assertEqual(result['points'][-1]['nominalLeadHours'], 6)

    def test_duplicate_receipt_rejected_and_invalid_quality_not_carried(self):
        self.manifest.append(self.manifest[0])
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            live.load_inputs(self.out, self.ref, self.now)
        self.manifest.pop()
        path = self.out / 'raw' / 'ana-86510000-fresh.xml'
        path.write_text(path.read_text().replace('Dado aprovado', 'Dado bruto', 1))
        next(r for r in self.manifest if r['file'] == path.name)['sha256'] = sha(path)
        self.write_manifest()
        _, data, _ = live.load_inputs(self.out, self.ref, self.now)
        self.assertTrue(np.isnan(data['86510000:H'][-1]))
        self.assertEqual(data['86510000:H'][-2], 12)

    def test_receipt_must_declare_its_timezone(self):
        self.manifest[0]['collected_at'] = '2026-09-23T10:14:00'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'receipt timezone required'):
            live.load_inputs(self.out, self.ref, self.now)

    def test_freshness_is_rechecked_at_actual_completion(self):
        self.manifest[0]['collected_at'] = (self.now-timedelta(minutes=59)).isoformat()
        self.write_manifest()
        with patch.object(live, 'datetime') as clock, patch.object(live, 'predict', side_effect=self.prediction):
            clock.now.side_effect = [self.now, self.now+timedelta(minutes=2)]
            clock.fromisoformat.side_effect = datetime.fromisoformat
            result = live.run_shadow(self.out, self.root, self.ref)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['points'], [])
        self.assertIn('freshness limit during inference', result['reason'])


if __name__ == '__main__':
    unittest.main()
