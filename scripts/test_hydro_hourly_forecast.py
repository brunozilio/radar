import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import hydro_hourly_forecast as hourly
import hydro_prospective_ledger as ledger
from hydro_routing_fit import fit_ridge


class HourlyForecastTests(unittest.TestCase):
    def test_saved_ridge_matches_existing_solver_with_missing_features(self):
        rng=np.random.default_rng(7)
        X=rng.normal(size=(180,6));X[::7,2]=np.nan
        y=np.nan_to_num(X[:,2])*3+X[:,0]*2+rng.normal(size=180)
        tr=np.arange(150);weights=1+2*(y>1)
        saved=hourly.ridge_fit(X,y,tr,1000.,weights)
        expected=fit_ridge(X,y,tr,np.arange(150,180),1000.,weights)
        np.testing.assert_allclose([hourly.ridge_predict(saved,x) for x in X[150:]],expected,atol=1e-12)

    def fixture(self,path,values,field='precipitation',offset=-10800,unit='mm'):
        path.write_text(json.dumps([{'utc_offset_seconds':offset,'hourly_units':{field:unit},'hourly':{'time':['2026-09-21T16:00','2026-09-21T17:00'],field:values}}]))

    def test_exact_weather_times_and_missing_values(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'weather.json';self.fixture(p,[2,None])
            times=[hourly.epoch(f'2026-09-21T{h}:00-03:00') for h in [16,17,18]]
            np.testing.assert_allclose(hourly.weather_values(p,0,times,'precipitation'),[2,np.nan,np.nan],equal_nan=True)

    def test_weather_rejects_wrong_timezone_units_and_negative_rain(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'weather.json'
            for values,offset,unit in [([1,2],0,'mm'),([1,2],-10800,'cm'),([-1,2],-10800,'mm')]:
                self.fixture(p,values,offset=offset,unit=unit)
                with self.assertRaises(ValueError):hourly.weather_values(p,0,[hourly.epoch('2026-09-21T16:00-03:00')],'precipitation')

    def test_live_weather_changes_only_current_feature_row(self):
        def read(path,loc,targets,field):
            return np.full(len(targets),1. if field=='precipitation_previous_day1' else 2.)
        with patch.object(hourly,'weather_values',side_effect=read):
            x=hourly.weather_features(np.array([0,3600,7200]),Path('/unused'))
        np.testing.assert_array_equal(x[:2],np.tile([3,6,9,12],(2,15)))
        np.testing.assert_array_equal(x[-1],np.tile([6,12,18,24],15))

    def test_missing_live_weather_cannot_become_zero_rain(self):
        def read(path,loc,targets,field):
            return np.full(len(targets),1. if field=='precipitation_previous_day1' else np.nan)
        with patch.object(hourly,'weather_values',side_effect=read):
            with self.assertRaises(ValueError):hourly.weather_features(np.array([0,3600]),Path('/unused'))

    def test_failed_cycle_is_preserved_and_does_not_issue_forecast(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch('sys.argv',['runner','--ledger',str(root)]),patch.object(hourly,'execute',side_effect=ValueError('missing required source')):
                with self.assertRaises(ValueError):hourly.run()
            records=ledger.read_records(root)
            self.assertEqual([r['kind'] for r in records],['cycle_started','cycle_failed'])
            self.assertEqual(records[-1]['payload']['cycle_sha256'],records[0]['sha256'])

    def test_completed_hour_is_not_counted_twice(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);ref=hourly.datetime.now(hourly.TZ).replace(minute=0,second=0,microsecond=0).isoformat()
            for model in ['radar_arvores_live_candidate']:
                ledger.append(root,'forecast_issue',{'model_id':model,'reference_at':ref})
            with patch('sys.argv',['runner','--ledger',str(root)]),patch.object(hourly,'execute') as execute,patch('builtins.print'):
                hourly.run();execute.assert_not_called()
            self.assertEqual(len(ledger.read_records(root)),1)

    def test_explicit_revision_keeps_original_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);ref=hourly.datetime.now(hourly.TZ).replace(minute=0,second=0,microsecond=0).isoformat()
            prior={}
            for model in ['radar_arvores_live_candidate']:
                prior[model]=ledger.append(root,'forecast_issue',{'model_id':model,'reference_at':ref})['sha256']
            with patch('sys.argv',['runner','--ledger',str(root),'--revision-reason','User requested latest observation','--require-observation-at',ref]),patch.object(hourly,'execute') as execute,patch.object(ledger,'report'):
                hourly.run()
            self.assertEqual(execute.call_args.args[0].revision['previous_forecasts'],prior)
            self.assertEqual([r['kind'] for r in ledger.read_records(root)],['forecast_issue','cycle_started','cycle_completed'])

    def test_required_observation_cannot_fall_back_to_older_level(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'raw').mkdir()
            (root/'collection-manifest.json').write_text('[]')
            (root/'raw/ana-86510000-fresh.xml').write_text('<root><row><CodEstacao>86510000</CodEstacao><DataHora>2026-09-21 17:30:00</DataHora><NivelFinal>1345</NivelFinal><CQ_NivelFinal>Dado aprovado</CQ_NivelFinal></row></root>')
            args=SimpleNamespace(source=root,require_observation_at='2026-09-21T18:00:00-03:00')
            with patch.object(hourly,'calculate') as calculate:
                with self.assertRaisesRegex(ValueError,'Required exact approved'):
                    hourly.execute(args)
                calculate.assert_not_called()

if __name__=='__main__':unittest.main()
