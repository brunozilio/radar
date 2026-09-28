"""Late telemetry selects its true hour; it never manufactures future targets."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import hydro_site_projection as site
import hydro_encantado as cities
from hydro_history import TZ, sha
from hydro_input_readiness import (select_latest_ready, InputsNotReady, LEVELS, PLANTS, GROUPS)
from hydro_feature_contract import feature_definitions, validate_snapshot


class DelayedReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source';(self.source/'raw').mkdir(parents=True)
        self.checked = datetime(2026,9,23,10,tzinfo=TZ)
        self.now = self.checked+timedelta(minutes=15)
        self.weights = self.source/'chuva-pesos.json'
        self.weights.write_text(json.dumps([{'group':g,'weights':{LEVELS[0]:.6,LEVELS[1]:.4}} for g in GROUPS]))
        self.prepare_source()

    def prepare_source(self, last_hour_ago=1, missing_plant_at=None):
        for code in LEVELS:
            rows=[]
            for minute in range(-4*60,-last_hour_ago*60+1,15):
                instant=self.checked+timedelta(minutes=minute)
                rows.append(f'<DadosHidrometereologicos><CodEstacao>{code}</CodEstacao><DataHora>{instant.isoformat()}</DataHora><NivelFinal>1000</NivelFinal><CQ_NivelFinal>Dado aprovado</CQ_NivelFinal><ChuvaFinal>0</ChuvaFinal><CQ_ChuvaFinal>Dado aprovado</CQ_ChuvaFinal></DadosHidrometereologicos>')
            (self.source/'raw'/f'ana-{code}-fresh.xml').write_text('<root>'+''.join(rows)+'</root>')
        for plant in PLANTS:
            rows=[]
            for hours in range(4,last_hour_ago-1,-1):
                if missing_plant_at==(plant,hours):
                    continue
                instant=self.checked-timedelta(hours=hours)
                cells=[instant.strftime('%d/%m/%Y %H:%M:%S'),'0','0','100','0','0','0','100']
                rows.append('<tr>'+''.join(f'<td>{v}</td>' for v in cells)+'</tr>')
            (self.source/'raw'/f'ceran-{plant}-fresh.html').write_text(''.join(rows))
        for model in site.NWP_MODELS:
            (self.source/'raw'/f'weather-{model}.json').write_text('[]')
        manifest=[{'file':p.name,'source':'ANA' if p.suffix=='.xml' else 'CERAN' if p.suffix=='.html' else 'Open-Meteo',
                   'collected_at':(self.checked+timedelta(minutes=10)).isoformat(),'sha256':sha(p)}
                  for p in (self.source/'raw').iterdir()]
        (self.source/'collection-manifest.json').write_text(json.dumps(manifest))

    def select(self, **changes):
        return select_latest_ready(self.source,self.checked,self.weights,now=self.now,**changes)

    def points(self, reference):
        return [{'timestamp':(reference+timedelta(hours=h)).isoformat(),'level':float(h)} for h in range(1,7)]

    def test_latest_complete_hour_is_selected_after_delayed_receipts(self):
        reference, report=self.select(after_reference=self.checked-timedelta(hours=3))
        self.assertEqual(reference,self.checked-timedelta(hours=1))
        self.assertEqual(report['status'],'ready')
        selection=json.loads((self.source/'reference-selection.json').read_text())
        self.assertEqual([c['status'] for c in selection['candidates']],['waiting_for_data','ready'])
        self.assertEqual(selection['checkedReferenceAt'],self.checked.isoformat())
        self.assertEqual(selection['selectedReferenceAt'],reference.isoformat())
        self.assertEqual(len(report['levels']),4)
        self.assertEqual(len(report['flows']),3)
        self.assertEqual(len(report['rainCoverage']),5)

    def test_a_missing_exact_plant_hour_chooses_older_complete_hour(self):
        self.prepare_source(missing_plant_at=('julho',1))
        reference, report=self.select(after_reference=self.checked-timedelta(hours=3))
        self.assertEqual(reference,self.checked-timedelta(hours=2))
        self.assertEqual(report['flows']['julho'],[100.,100.])
        self.assertTrue(any('outflow/inflow missing' in error for error in report['referenceSelection']['candidates'][1]['missing']))

    def test_already_published_hour_cannot_be_selected_or_revised(self):
        with self.assertRaises(InputsNotReady) as caught:
            self.select(after_reference=self.checked-timedelta(hours=1))
        self.assertIsNone(caught.exception.report['referenceSelection']['selectedReferenceAt'])
        self.assertEqual(caught.exception.report['referenceSelection']['candidates'][1]['status'],'already_published')

    def test_age_uses_actual_clock_not_floor_hour(self):
        self.prepare_source(last_hour_ago=3)
        with self.assertRaises(InputsNotReady) as caught:
            self.select()
        last=caught.exception.report['referenceSelection']['candidates'][-1]
        self.assertEqual(last['status'],'reference_too_old')
        self.assertEqual(last['referenceAgeSeconds'],3*3600+15*60)

    def test_future_suffix_preserves_nominal_targets_and_values(self):
        reference=self.checked-timedelta(hours=2)
        original=self.points(reference)
        before=copy.deepcopy(original)
        remaining=site.future_model_points(reference,original,self.now)
        self.assertEqual(remaining,original[2:])
        self.assertEqual([p['level'] for p in remaining],[3.,4.,5.,6.])
        self.assertEqual(original,before)
        self.assertEqual(site.future_model_points(reference,original,reference+timedelta(hours=3)),original[3:])
        with self.assertRaises(InputsNotReady):
            site.future_model_points(reference,original,reference+timedelta(hours=3,microseconds=1))
        with self.assertRaises(ValueError):
            site.future_model_points(reference,original[3:],reference+timedelta(hours=2,minutes=15))

    def test_city_delay_is_opt_in_and_never_changes_observation_hour(self):
        reference=self.checked-timedelta(hours=1)
        issue={'referenceAt':reference.isoformat(),'generatedAt':self.now.isoformat(),
               'observation':{'timestamp':reference.isoformat(),'level':10.},
               'models':[{'points':self.points(reference)}]}
        with self.assertRaises(ValueError):
            cities.remaining_targets(copy.deepcopy(issue),reference,False)
        result=cities.remaining_targets(copy.deepcopy(issue),reference,True)
        self.assertEqual(result['referenceAt'],issue['referenceAt'])
        self.assertEqual(result['observation'],issue['observation'])
        self.assertEqual(result['forecastStartLeadHours'],2)
        self.assertEqual(result['models'][0]['points'],issue['models'][0]['points'][1:])
        self.assertEqual(result['referenceAgeSeconds'],75*60)

    def test_perform_attempt_emits_selected_hour_and_future_suffix(self):
        state=self.root/'state';state.mkdir()
        out=self.root/'attempt';out.mkdir()
        history=out/'history';history.mkdir();(history/'manifest.json').write_text('{}')
        args=SimpleNamespace(source=self.source,state=state,attempt_id='fixture',
                             after_reference=self.checked-timedelta(hours=3))
        reference=self.checked-timedelta(hours=1)
        def calculate(folder, selected):
            self.assertEqual(selected,reference)
            (folder/'model-metadata.json').write_text('{}')
            return {'value':10.,'last_time':selected.isoformat()},self.points(selected)
        def record(folder,*_args):
            (folder/'feature-snapshot.json').write_text('{}')
            (folder/'short-term-shadow.json').write_text('{"status":"unavailable"}')
        with patch.object(site,'PREV',self.source), patch.object(site,'datetime') as clock, \
             patch('hydro_input_readiness.datetime') as gate_clock, \
             patch.dict('os.environ',{'OBJECT_STORAGE_URL':''}), \
             patch.object(site.hydro_history,'build',return_value=history) as build, \
             patch.object(site,'calculate_model',side_effect=calculate), \
             patch.object(site,'record_features_and_shadow',side_effect=record), \
             patch.object(cities,'calculate',side_effect=AssertionError('Retired city forecast called')) as city_calculate:
            clock.now.return_value=self.now;clock.fromisoformat.side_effect=datetime.fromisoformat
            gate_clock.now.return_value=self.now
            payload=site.perform_legacy_attempt(args,out,self.checked)
        city_calculate.assert_not_called()
        self.assertEqual(payload['station'],'mucum')
        self.assertNotIn('encantado',payload)
        self.assertNotIn('santa-tereza',payload)
        self.assertEqual(payload['referenceAt'],reference.isoformat())
        self.assertEqual(payload['checkedReferenceAt'],self.checked.isoformat())
        self.assertEqual(payload['forecastStartLeadHours'],2)
        self.assertEqual(payload['horizonHours'],6)
        self.assertEqual(payload['referenceAgeSeconds'],75*60)
        self.assertEqual(payload['models'][0]['points'],self.points(reference)[1:])
        self.assertEqual(args.selected_reference,reference)
        self.assertTrue(build.call_args.kwargs['allow_missing_rain'])
        self.assertTrue((out/'reference-selection.json').is_file())

    def test_delayed_snapshot_is_v2_and_shadow_remains_unavailable(self):
        reference, readiness=self.select()
        values=[max(0.,field['minimum'] or 0.) for field in feature_definitions()]
        for index,code in enumerate(LEVELS):
            values[index*6]=readiness['levels'][code]
        for index,plant in enumerate(PLANTS):
            q,inflow=readiness['flows'][plant]
            values[24+7*index:27+7*index]=[(q/1000)**.6,q/1000,inflow/1000]
        (self.source/'current-features.json').write_text(json.dumps(values))
        (self.source/'model-metadata.json').write_text(json.dumps({
            'trainingFeatureContract':'legacy-mixed-nwp-unverified','model':{'id':'frozen-fixture'}}))
        points=site.future_model_points(reference,self.points(reference),self.now)
        site.record_features_and_shadow(self.source,reference,self.now.isoformat(),{'value':10.},points)
        snapshot=json.loads((self.source/'feature-snapshot.json').read_text())
        shadow=json.loads((self.source/'short-term-shadow.json').read_text())
        self.assertEqual(snapshot['contract_id'],'radar-180-contemporaneous/v2')
        self.assertEqual(snapshot['reference_age_seconds'],75*60)
        self.assertEqual(validate_snapshot(snapshot),[])
        self.assertEqual(snapshot['reference_at'],reference.isoformat())
        self.assertEqual(snapshot['model']['referenceSelection']['checkedReferenceAt'],self.checked.isoformat())
        self.assertEqual(shadow['status'],'unavailable')
        self.assertEqual(shadow['points'],[])
        self.assertFalse(shadow['publishable'])


if __name__=='__main__':
    unittest.main()
