"""Targeted regression checks for the rainfall accounting defect."""
import unittest
import numpy as np
from hydro_rain_windows import observed_rain_windows

class RainWindowsTests(unittest.TestCase):
    def test_no_reuse_in_following_hour(self):
        r=observed_rain_windows(np.array([0.,3600.,7200.]),np.array([0.,0.,25.8]),np.array([7200.,10800.]),[1,2])
        np.testing.assert_allclose(r[1][0],[25.8,0]);np.testing.assert_allclose(r[1][1],[1,0]);np.testing.assert_allclose(r[2][0],[25.8,25.8])
    def test_future_rain_does_not_change_past(self):
        t=np.arange(20)*900.;p=np.arange(20,dtype=float);grid=t[:12]
        a=observed_rain_windows(t,p,grid);p[12:]=1000;b=observed_rain_windows(t,p,grid)
        for w in a:
            np.testing.assert_allclose(a[w][0],b[w][0]);np.testing.assert_allclose(a[w][1],b[w][1])
    def test_partial_hour_preserves_unknown_tail(self):
        r=observed_rain_windows(np.array([0.,3600.,7200.]),np.array([0.,8.,12.]),np.array([8100.]),[1])[1]
        np.testing.assert_allclose(r[0],[9]);np.testing.assert_allclose(r[1],[.75])
    def test_suspect_and_missing_are_not_dry(self):
        r=observed_rain_windows(np.array([0.,3600.,7200.]),np.array([0.,np.nan,0.]),np.array([7200.]),[2])[2]
        np.testing.assert_allclose(r[0],[0]);np.testing.assert_allclose(r[1],[.5])
    def test_long_gap_is_not_an_observed_interval(self):
        r=observed_rain_windows(np.array([0.,10800.]),np.array([0.,30.]),np.array([10800.]),[3])[3]
        np.testing.assert_allclose(r[0],[0]);np.testing.assert_allclose(r[1],[0])
    def test_totals_increase_with_window_length(self):
        r=observed_rain_windows(np.arange(25)*900.,np.ones(25),np.array([21600.]),[1,3,6])
        np.testing.assert_allclose([r[w][0][0] for w in [1,3,6]],[4,12,24])

if __name__=='__main__':unittest.main()
