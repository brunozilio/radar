import unittest
import numpy as np
from hydro_past_error_calibration import past_error_correction

class PastErrorTest(unittest.TestCase):
    def test_target_requires_observation_delay_and_future_values_cannot_affect_past(self):
        times=np.arange(8)*3600.;targets=times+3600;forecast=np.full(8,10.);actual=np.full(8,8.)
        got,_,counts,latest,_=past_error_correction(times,targets,forecast,actual,minimum=1)
        np.testing.assert_array_equal(got[:3],[10.,10.,8.])
        actual[3:]=1000.
        second=past_error_correction(times,targets,forecast,actual,minimum=1)[0]
        np.testing.assert_array_equal(got[:5],second[:5])
        self.assertEqual(latest[2],3600.)

    def test_cold_start_minimum_and_original_errors_not_corrected_errors(self):
        times=np.arange(12)*3600.;targets=times+3600;forecast=np.full(12,10.);actual=np.full(12,8.)
        got,correction,count,_,_=past_error_correction(times,targets,forecast,actual,minimum=3)
        np.testing.assert_array_equal(got[:4],[10.,10.,10.,10.])
        np.testing.assert_array_equal(got[4:],np.full(8,8.))
        np.testing.assert_array_equal(correction[4:],np.full(8,2.))

    def test_expired_or_missing_errors_do_not_fill_missing_forecasts(self):
        times=np.array([0.,3600.,30*3600]);targets=times+3600
        got,_,counts,_,_=past_error_correction(times,targets,np.array([10.,np.nan,10.]),np.array([8.,8.,8.]),minimum=1)
        self.assertTrue(np.isnan(got[1]));self.assertEqual(counts[-1],0);self.assertEqual(got[-1],10.)

    def test_unsorted_or_nonfuture_targets_rejected(self):
        for times,targets in [([3600.,0.],[7200.,3600.]),([0.,3600.],[0.,7200.])]:
            with self.assertRaises(ValueError):past_error_correction(times,targets,[10.,10.],[8.,8.])

if __name__=='__main__':unittest.main()
