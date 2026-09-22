import unittest
import numpy as np
from hydro_rating_paired_fit import fit_curve,replace_curve
from hydro_downstream_flow_delta import stage

class RatingPairedTest(unittest.TestCase):
    def test_curve_fit_ignores_targets_outside_training(self):
        q=np.linspace(.1,8,100);h=4.5*q**.64+.4;idx=np.arange(60)
        first,_=fit_curve(q,h,idx);h[60:]=999;q[60:]=888
        second,_=fit_curve(q,h,idx);np.testing.assert_array_equal(first,second)
        with self.assertRaises(ValueError):fit_curve(np.array([np.nan]),np.array([2.]),np.array([0]))

    def test_replacement_preserves_flow_and_anchor_under_new_curve(self):
        old=[4.5,.6,.4];new=[4.,.7,.2];ah=7.;aq=2000.;q=5000.
        base=float(stage(q,old)+ah-stage(aq,old))
        value,recovered=replace_curve(base,ah,aq,old,new)
        self.assertAlmostEqual(recovered,q,places=9)
        self.assertAlmostEqual(value,float(stage(q,new)+ah-stage(aq,new)),places=12)
        anchored,_=replace_curve(ah,ah,aq,old,new);self.assertAlmostEqual(anchored,ah,places=12)
        self.assertTrue(np.isnan(replace_curve(np.nan,ah,aq,old,new)[0]))

if __name__=='__main__':unittest.main()
