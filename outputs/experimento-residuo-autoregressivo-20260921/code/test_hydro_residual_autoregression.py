import unittest
import numpy as np

from hydro_residual_autoregression import features, fit, predict, corrected_level


class ResidualAutoregressionTest(unittest.TestCase):
    def test_feature_prefix_cannot_read_future_finalized_residual(self):
        finalized=np.arange(200,dtype=float)
        anchor=finalized+100
        expected=features(anchor,finalized)
        for at in (6,50,199):
            other=finalized.copy();other[at:]=1e9
            other_anchor=anchor.copy();other_anchor[at+1:]=1e10
            np.testing.assert_array_equal(features(other_anchor,other)[at],expected[at])
            np.testing.assert_array_equal(expected[at],[anchor[at],finalized[at-1],finalized[at-3],finalized[at-6]])

    def test_cutoff_excludes_target_at_boundary_and_later(self):
        rng=np.random.default_rng(410)
        X=rng.normal(size=(200,4));y=X[:,0]*7-X[:,2];times=np.arange(200)
        model,mask=fit(X,y,times,150)
        self.assertEqual(mask.sum(),150)
        X2=X.copy();X2[150:]=1e8;y2=y.copy();y2[150:]=-1e12
        second,mask2=fit(X2,y2,times,150)
        for key in model:np.testing.assert_array_equal(model[key],second[key])
        self.assertFalse(mask2[150])
        self.assertTrue(np.isfinite(predict(model,X[:4])).all())

    def test_fallback_preserves_original_and_invalid_q_never_clipped(self):
        rating=[4.,.6,.4]
        self.assertEqual(corrected_level(8.,1000.,np.nan,0.,rating),(8.,'fallback_original_tau6'))
        self.assertEqual(corrected_level(None,1000.,200.,0.,rating),(None,'baseline_missing'))
        self.assertEqual(corrected_level(8.,100.,-101.,0.,rating),(None,'invalid_candidate_flow'))
        level,status=corrected_level(8.,1000.,-100.,.2,rating)
        self.assertEqual(status,'candidate_applied')
        self.assertAlmostEqual(level,4.*.9**.6+.6)


if __name__=='__main__':unittest.main()
