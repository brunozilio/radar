import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import hydro_prospective_ledger as ledger


def time(hhmm):
    return ledger.timestamp(f'2026-09-21T{hhmm}:00+00:00')


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.model=self.root/'model.json';self.model.write_text('{"test":true}')
        blob,sha=ledger.store_blob(self.root,b'input','txt')
        with patch.object(ledger,'now',return_value=time('16:10')):
            self.input=ledger.append(self.root,'input_receipt',{'blob':blob,'blob_sha256':sha})
        self.packet={'station_id':'86510000','datum_id':'test-datum','model_id':'reference','model_version':'v1',
                     'reference_at':time('16:00').isoformat(),'produced_at':time('16:15').isoformat(),
                     'training_cutoff':time('15:00').isoformat(),'input_receipts':[self.input['sha256']],
                     'model_artifacts':[{'path':str(self.model),'sha256':ledger.digest(self.model.read_bytes())}],
                     'points':[{'valid_at':time('18:00').isoformat(),'nominal_lead_h':2,'level_m':8.}]}

    def tearDown(self):self.temp.cleanup()

    def issue(self, archival=False):
        with patch.object(ledger,'now',return_value=time('16:30')):
            return ledger.register_forecast(self.root,self.packet,archival)

    def observe(self, quality='Dado aprovado', at='18:15', datum='test-datum', level=8.5):
        raw=json.dumps({'level':level,'quality':quality}).encode()
        blob,sha=ledger.store_blob(self.root,raw,'json')
        with patch.object(ledger,'now',return_value=time(at)):
            return ledger.append(self.root,'observation_receipt',{'blob':blob,'blob_sha256':sha,'observations':[
                {'station_id':'86510000','datum_id':datum,'valid_at':time('18:00').isoformat(),
                 'quality':quality,'level_m':level,'timezone_verified':True,'datum_verified':True}]})

    def test_retired_hge_cannot_be_issued_or_imported(self):
        for model in ['hge_arno_live_candidate','hge_arno_reference','arno']:
            self.packet['model_id']=model
            for archival in [False,True]:
                with self.assertRaisesRegex(ValueError,'removed'):
                    self.issue(archival)
        self.assertEqual(len(ledger.read_records(self.root)),1)

    def test_active_report_omits_retired_models_without_deleting_receipts(self):
        self.packet['model_id']='radar_arvores_live_candidate'
        self.issue(); self.observe()
        with patch.object(ledger,'now',return_value=time('18:30')):
            old={**self.packet,'model_id':'hge_arno_live_candidate'}
            ledger.append(self.root,'forecast_issue',old)
        before=ledger.read_records(self.root)
        with patch.object(ledger,'now',return_value=time('19:00')),patch('builtins.print'):
            out=ledger.report(self.root)
        self.assertEqual(ledger.read_records(self.root),before)
        self.assertNotIn('hge', (out/'verification.csv').read_text())
        self.assertEqual(json.loads((out/'summary.json').read_text())['retired_model_pairs_preserved'],1)

    def test_real_lead_not_nominal_and_threshold_inclusive(self):
        self.issue();self.observe()
        result=ledger.evaluate(self.root,time('19:00'))[0]
        self.assertTrue(result['goal_eligible']);self.assertTrue(result['hit_within_050m'])
        self.assertEqual(result['minimum_verified_lead_h'],1)
        self.assertEqual(result['actual_lead_h'],1.5)
        self.assertTrue(result['shorter_than_nominal_lead'])

    def test_old_import_never_becomes_prospective(self):
        self.issue(archival=True);self.observe()
        result=ledger.evaluate(self.root,time('19:00'))[0]
        self.assertFalse(result['goal_eligible']);self.assertIn('archival_import',result['exclusion_reasons'])

    def test_manual_revision_preserves_original_and_does_not_double_count(self):
        original=self.issue()
        self.packet['manual_revision']={'previous_forecast':original['sha256']}
        self.packet['points'][0]['level_m']=9.
        self.issue();self.observe()
        original,revision=ledger.evaluate(self.root,time('19:00'))
        self.assertEqual(original['forecast_m'],8.)
        self.assertTrue(original['goal_eligible'])
        self.assertEqual(revision['forecast_m'],9.)
        self.assertEqual(revision['status'],'matched')
        self.assertFalse(revision['goal_eligible'])
        self.assertIn('manual_revision_outside_scheduled_sample',revision['exclusion_reasons'])

    def test_historical_snapshot_cannot_see_later_issuance(self):
        self.issue()
        self.assertEqual(ledger.evaluate(self.root,time('16:20')),[])

    def test_observation_revision_only_applies_after_its_receipt(self):
        self.issue();self.observe();self.observe('Dado suspeito',at='18:30',level=9.)
        earlier=ledger.evaluate(self.root,time('18:20'))[0]
        later=ledger.evaluate(self.root,time('18:40'))[0]
        self.assertTrue(earlier['goal_eligible'])
        self.assertEqual(earlier['observed_m'],8.5)
        self.assertFalse(later['goal_eligible'])

    def test_backdate_field_rejected(self):
        self.packet['issued_at']=time('15:00').isoformat()
        with self.assertRaises(ValueError):self.issue()

    def test_unknown_or_changed_inputs_rejected(self):
        self.packet['input_receipts']=['unknown']
        with self.assertRaises(ValueError):self.issue()
        self.packet['input_receipts']=[self.input['sha256']]
        self.model.write_text('changed')
        with self.assertRaises(ValueError):self.issue()

    def test_cycle_must_exist_and_precede_production(self):
        self.packet['cycle_sha256']='unknown'
        with self.assertRaises(ValueError):self.issue()
        with patch.object(ledger,'now',return_value=time('16:20')):
            cycle=ledger.append(self.root,'cycle_started',{})
        self.packet['cycle_sha256']=cycle['sha256']
        with self.assertRaises(ValueError):self.issue()

    def test_valid_cycle_is_preserved_in_issue(self):
        with patch.object(ledger,'now',return_value=time('16:12')):
            cycle=ledger.append(self.root,'cycle_started',{})
        self.packet['cycle_sha256']=cycle['sha256']
        result=self.issue()
        self.assertEqual(result['payload']['cycle_sha256'],cycle['sha256'])

    def test_revision_to_bad_quality_removes_previous_match(self):
        self.issue();self.observe();self.observe('Dado suspeito',at='18:30',level=9.)
        result=ledger.evaluate(self.root,time('19:00'))[0]
        self.assertFalse(result['goal_eligible'])
        self.assertEqual(result['status'],'invalid_or_unapproved_observation')

    def test_wrong_datum_does_not_pair(self):
        self.issue();self.observe(datum='another-datum')
        result=ledger.evaluate(self.root,time('19:00'))[0]
        self.assertEqual(result['status'],'missing_exact_observation')

    def test_future_observation_not_ground_truth(self):
        self.issue();self.observe(at='17:00')
        result=ledger.evaluate(self.root,time('19:00'))[0]
        self.assertEqual(result['status'],'missing_exact_observation')

    def test_local_tampering_detected(self):
        self.issue()
        path=sorted((self.root/'records').glob('*.json'))[-1]
        data=json.loads(path.read_text());data['record']['payload']['points'][0]['level_m']=7
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):ledger.read_records(self.root)

    def test_missing_observation_is_not_a_hit(self):
        self.issue()
        result=ledger.evaluate(self.root,time('19:00'))[0]
        self.assertFalse(result['goal_eligible']);self.assertIsNone(result['hit_within_050m'])

    def test_station_identity_and_centimeter_conversion(self):
        xml=b'<root><DadosHidrometereologicos><CodEstacao>86510000</CodEstacao><DataHora>2026-09-21 16:00:00</DataHora><NivelFinal>1164</NivelFinal><CQ_NivelFinal>Dado aprovado</CQ_NivelFinal></DadosHidrometereologicos></root>'
        rows=ledger.parse_ana(xml,'86510000','test-datum')
        self.assertEqual(rows[0]['level_m'],11.64)
        self.assertFalse(rows[0]['datum_verified'])
        self.assertEqual(ledger.parse_ana(xml,'99999','test-datum'),[])


if __name__=='__main__':unittest.main()
