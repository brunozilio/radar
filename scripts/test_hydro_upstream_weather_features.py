import unittest
import numpy as np
from hydro_upstream_weather_features import complete_future_totals,forecast_lookup,future_rain_features,FIELD
from hydro_hourly_forecast import epoch

class WeatherFeaturesTest(unittest.TestCase):
    def test_ensemble_excludes_partial_members_and_preserves_empty_windows(self):
        weather=[]
        for amount in (1.,2.,3.):
            locations=[]
            for group in range(5):
                values=[amount]*13
                if group==0 and amount==1.:values[1]=None
                if group==1:values[2]=None
                locations.append({'utc_offset_seconds':-10800,'hourly_units':{FIELD:'mm'},
                                  'hourly':{'time':[f'2026-01-01T{h:02}:00' for h in range(13)],FIELD:values}})
            weather.append(locations)
        X,counts,names=future_rain_features(weather,np.array([epoch('2026-01-01T00:00')]))
        self.assertEqual(X.shape,(1,20))
        np.testing.assert_allclose(X[0,:4],[.075,.15,.225,.3])
        np.testing.assert_array_equal(counts[0,:4],[2,2,2,2])
        self.assertTrue(np.isnan(X[0,4:8]).all())
        np.testing.assert_array_equal(counts[0,4:8],[0,0,0,0])
        self.assertEqual(len(names),20)

    def test_window_excludes_origin_and_values_beyond_horizon(self):
        lookup={0:999.,3600:1.,7200:2.,10800:3.,14400:999.}
        np.testing.assert_array_equal(complete_future_totals(lookup,np.array([0]),3),[6.])
        lookup[0]=1e10;lookup[14400]=1e10
        np.testing.assert_array_equal(complete_future_totals(lookup,np.array([0]),3),[6.])

    def test_partial_window_is_missing_not_zero(self):
        lookup={3600:1.,7200:2.}
        self.assertTrue(np.isnan(complete_future_totals(lookup,np.array([0]),3)[0]))
        lookup[10800]=None
        self.assertTrue(np.isnan(complete_future_totals(lookup,np.array([0]),3)[0]))

    def test_observed_field_never_substitutes_for_forecast(self):
        location={'utc_offset_seconds':-10800,'hourly_units':{FIELD:'mm'},'hourly':{'time':['2026-01-01T00:00'],'precipitation':[20.]}}
        with self.assertRaises(ValueError):forecast_lookup(location)
        location['hourly'][FIELD]=[None]
        self.assertTrue(np.isnan(next(iter(forecast_lookup(location).values()))))
        location['hourly']['time']*=2;location['hourly'][FIELD]=[0.,0.]
        with self.assertRaises(ValueError):forecast_lookup(location)

if __name__=='__main__':unittest.main()
