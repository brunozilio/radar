import unittest
import numpy as np
from hydro_flow_change_clipping import fit_bounds,apply_bounds

class ClippingTest(unittest.TestCase):
    def test_future_extremes_cannot_change_training_bounds(self):
        X=np.array([[1.,2.],[2.,4.],[3.,6.],[100.,200.]])
        bounds=fit_bounds(X,np.array([0,1,2]),[1])
        X[-1,1]=1e12
        self.assertEqual(bounds,fit_bounds(X,np.array([0,1,2]),[1]))
        result=apply_bounds(X,bounds,[1])
        np.testing.assert_array_equal(result[:,0],X[:,0])
        self.assertEqual(result[-1,1],bounds[0][1])
        self.assertEqual(X[-1,1],1e12)

    def test_missing_and_zero_observations_remain_intact(self):
        X=np.array([[0.,np.nan],[2.,-3.],[4.,3.]])
        result=apply_bounds(X,[[-1.,1.]],[1])
        self.assertTrue(np.isnan(result[0,1]))
        np.testing.assert_array_equal(result[:,0],X[:,0])
        np.testing.assert_allclose(result[1:,1],[-1.,1.])
        self.assertEqual(fit_bounds(X,np.array([0]),[1]),[[None,None]])
        np.testing.assert_array_equal(apply_bounds(X,[[None,None]],[1]),X)

    def test_invalid_or_reversed_bounds_rejected(self):
        for bounds in [[],[[2.,1.]],[[None,1.]],[[0.,np.inf]]]:
            with self.assertRaises(ValueError):apply_bounds(np.zeros((2,2)),bounds,[1])

if __name__=='__main__':unittest.main()
