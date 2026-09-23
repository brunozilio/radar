import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import hydro_site_projection as site
import hydro_propagation_public as public
from hydro_input_readiness import InputsNotReady


class PublicHydrometryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.reference = datetime(2026, 9, 23, 12, tzinfo=timezone.utc)
        self.generated = self.reference + timedelta(minutes=15)
        self.shadow = dict(schema='radar-propagation-shadow/v1', mode='shadow', publishable=False,
            station='86510000', status='calculated', modelVersion=public.SOURCE_MODEL_VERSION,
            modelSha256=public.MODEL_SHA256, contract=public.CONTRACT, rainRequired=False,
            checkedReferenceAt=self.reference.isoformat(), referenceAt=self.reference.isoformat(),
            generatedAt=self.generated.isoformat(), referenceAgeSeconds=900,
            observation=dict(timestamp=self.reference.isoformat(), level=10.),
            sources=[dict(file=name, availableAt=(self.generated-timedelta(minutes=1)).isoformat(),
                          sha256='a'*64) for name in sorted(public.SOURCE_FILES)],
            points=[dict(timestamp=(self.reference+timedelta(hours=h)).isoformat(), level=10.+h/10,
                         nominalLeadHours=h, lower=9.+h/10, upper=11.+h/10) for h in range(1, 7)])

    def issue(self, value=None, **kwargs):
        return public.public_forecast(value or self.shadow, checked_reference=self.reference,
            attempt_id='test', now=kwargs.pop('now',self.generated), **kwargs)

    def test_complete_hydrometry_publishes_without_rain_or_nwp_and_preserves_source(self):
        original=copy.deepcopy(self.shadow)
        result=self.issue()
        self.assertEqual(self.shadow,original)
        self.assertEqual(result['modelVersion'],public.MODEL_VERSION)
        self.assertEqual(result['modelSha256'],public.MODEL_SHA256)
        self.assertEqual(result['models'][0]['id'],public.MODEL_ID)
        self.assertEqual(result['referenceAt'],self.shadow['referenceAt'])
        self.assertEqual(result['generatedAt'],self.shadow['generatedAt'])
        self.assertFalse(result['rainRequired'])
        self.assertTrue(result['experimental'])
        self.assertFalse(result['accuracy']['demonstrated'])
        self.assertEqual(result['models'][0]['points'][0]['realLeadHours'],.75)
        self.assertEqual(result['forecastStartLeadHours'],1)

    def test_missing_intrinsic_measurements_waits(self):
        value=copy.deepcopy(self.shadow)
        value.update(status='unavailable',reason='86510000:H missing',points=[])
        with self.assertRaises(InputsNotReady) as error:
            self.issue(value)
        self.assertFalse(error.exception.report['rainRequired'])
        self.assertEqual(error.exception.report['missing'],['86510000:H missing'])

    def test_old_reference_or_stale_sources_wait_without_fabricating_data(self):
        with self.assertRaises(InputsNotReady):
            self.issue(now=self.reference+timedelta(hours=3,microseconds=1))
        with self.assertRaises(InputsNotReady):
            self.issue(now=self.generated+timedelta(hours=1))
        value=copy.deepcopy(self.shadow)
        value['sources'][0]['availableAt']=(self.generated+timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):
            self.issue(value)

    def test_nominal_suffix_keeps_reference_and_generation(self):
        value=copy.deepcopy(self.shadow)
        issued=self.reference+timedelta(hours=2,minutes=15)
        value['generatedAt']=issued.isoformat()
        value['points']=value['points'][2:]
        for source in value['sources']:
            source['availableAt']=issued.isoformat()
        result=self.issue(value,now=issued)
        self.assertEqual(result['forecastStartLeadHours'],3)
        self.assertEqual(result['referenceAgeSeconds'],8100)
        self.assertEqual(result['models'][0]['points'][0]['nominalLeadHours'],3)
        self.assertEqual(result['models'][0]['points'][0]['realLeadHours'],.75)
        self.assertEqual(result['observation']['timestamp'],self.reference.isoformat())

    def test_crossing_target_hour_before_publication_requires_fresh_issue(self):
        original=copy.deepcopy(self.shadow)
        with self.assertRaises(InputsNotReady) as error:
            self.issue(now=self.reference+timedelta(hours=1))
        self.assertIn('expired before publication',error.exception.report['missing'][0])
        self.assertEqual(self.shadow,original)

    def test_expired_missing_or_duplicate_targets_rejected(self):
        for mutate in (lambda x:x['points'].pop(2),
                       lambda x:x['points'].insert(2,x['points'][1]),
                       lambda x:x['points'][0].update(timestamp=self.reference.isoformat(),nominalLeadHours=0),
                       lambda x:x['points'][0].update(level=float('nan'))):
            value=copy.deepcopy(self.shadow);mutate(value)
            with self.assertRaises(ValueError): self.issue(value)

    def test_unexpected_weights_station_timezone_or_anchor_rejected(self):
        for mutate in (lambda x:x.update(modelSha256='b'*64),
                       lambda x:x.update(station='86720000'),
                       lambda x:x.update(referenceAt='2026-09-23T12:00:00'),
                       lambda x:x['observation'].update(timestamp=(self.reference-timedelta(hours=1)).isoformat()),
                       lambda x:x['sources'].pop()):
            value=copy.deepcopy(self.shadow);mutate(value)
            with self.assertRaises((ValueError,KeyError)): self.issue(value)

    def test_equal_or_older_published_reference_not_reissued(self):
        for previous in (self.reference,self.reference+timedelta(hours=1)):
            with self.assertRaises(InputsNotReady): self.issue(after_reference=previous)
        self.assertEqual(self.issue(after_reference=self.reference-timedelta(hours=1))['referenceAt'],self.reference.isoformat())

    def setup_attempt(self):
        source=self.root/'source';(source/'raw').mkdir(parents=True)
        (source/'collection-manifest.json').write_text('[]')
        state=self.root/'state';state.mkdir()
        args=SimpleNamespace(source=source,state=state,attempt_id='test',after_reference=None)
        return args

    def fake_shadow(self,out,*_args):
        (out/'propagation-shadow.json').write_text(json.dumps(self.shadow))
        return copy.deepcopy(self.shadow)

    def test_primary_never_calls_legacy_rain_gate_or_fitting(self):
        args=self.setup_attempt();out=self.root/'out';out.mkdir()
        with patch.object(site,'run_propagation_shadow',side_effect=self.fake_shadow), \
             patch.object(site,'datetime') as clock, \
             patch.object(site,'select_latest_ready',side_effect=AssertionError('Rain gate called')), \
             patch.object(site,'calculate_model',side_effect=AssertionError('Legacy model called')), \
             patch.object(site.hydro_history,'build',side_effect=AssertionError('Legacy history called')):
            clock.now.return_value=self.generated;clock.fromisoformat.side_effect=datetime.fromisoformat
            result=site.perform_attempt(args,out,self.reference)
        self.assertEqual(args.selected_reference,self.reference)
        self.assertEqual(json.loads((out/'forecast.json').read_text()),result)
        self.assertEqual(json.loads((out/'propagation-shadow.json').read_text()),self.shadow)
        self.assertFalse((args.state/'history.tar.gz').exists())
        self.assertFalse((args.state/'audit.tar.gz').exists())
        self.assertFalse(result['inputReadiness']['rainRequired'])

    def test_result_only_saved_after_archive_and_archive_contains_both_documents(self):
        args=self.setup_attempt()
        runtime=self.root/'runtime';(runtime/'scripts').mkdir(parents=True)
        (runtime/'scripts'/'hydro-hourly-requirements.txt').write_text('')
        original_enqueue=site.enqueue_attempt
        def archive(*positional,**kwargs):
            self.assertFalse((args.state/'result.json').exists())
            return original_enqueue(*positional,**kwargs)
        with patch('sys.argv',['run','--state',str(args.state),'--source',str(args.source),
                               '--reference',self.reference.isoformat(),'--attempt-id','test']), \
             patch.object(site,'ROOT',runtime), patch.object(site,'datetime') as clock, \
             patch.object(site,'run_propagation_shadow',side_effect=self.fake_shadow), \
             patch.object(site,'enqueue_attempt',side_effect=archive):
            clock.now.return_value=self.generated;clock.fromisoformat.side_effect=datetime.fromisoformat
            site.main()
        result=json.loads((args.state/'result.json').read_text())
        status=json.loads((args.state/'refresh-status.json').read_text())
        receipt=json.loads((args.state/'archive'/'pending'/'test.json').read_text())
        self.assertEqual(result['archiveReceiptKey'],status['archiveReceiptKey'])
        self.assertEqual(receipt['status'],'calculated')
        attempt=next(x for x in receipt['objects'] if x['role']=='attempt')
        with tarfile.open(args.state/'archive'/'blobs'/f"{attempt['sha256']}.tar.gz",'r:gz') as tar:
            archived=json.load(tar.extractfile('forecast.json'))
            shadow=json.load(tar.extractfile('propagation-shadow.json'))
        self.assertEqual(archived,result)
        self.assertEqual(shadow,self.shadow)

    def test_failed_archive_cannot_save_public_result(self):
        args=self.setup_attempt()
        with patch('sys.argv',['run','--state',str(args.state),'--source',str(args.source),
                               '--reference',self.reference.isoformat(),'--attempt-id','test']), \
             patch.object(site,'datetime') as clock, \
             patch.object(site,'run_propagation_shadow',side_effect=self.fake_shadow), \
             patch.object(site,'enqueue_attempt',side_effect=OSError('Archive unavailable')):
            clock.now.return_value=self.generated;clock.fromisoformat.side_effect=datetime.fromisoformat
            with self.assertRaises(OSError): site.main()
        self.assertFalse((args.state/'result.json').exists())


if __name__=='__main__':
    unittest.main()
