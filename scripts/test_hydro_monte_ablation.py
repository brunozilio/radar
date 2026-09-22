import unittest
import numpy as np
from hydro_monte_ablation import without_monte


class MonteAblationTest(unittest.TestCase):
    def test_source_contract_preserves_other_plants_rain_and_nan(self):
        x=np.arange(154,dtype=float).reshape(2,77);x[0,3]=np.nan
        expected=np.concatenate([x[:,:8],x[:,16:61],x[:,69:]],axis=1)
        np.testing.assert_equal(without_monte(x),expected)
        changed=x.copy();changed[:,8:16]=np.nan;changed[:,61:69]=-999
        np.testing.assert_equal(without_monte(changed),expected)
        self.assertEqual(without_monte(x).shape,(2,61))
        y=without_monte(x);y[:]=0
        self.assertEqual(x[1,0],77);self.assertTrue(np.isnan(x[0,3]))

    def test_unrecognized_contract_is_rejected(self):
        for x in [np.zeros(77),np.zeros((2,53)),np.zeros((2,97))]:
            with self.assertRaises(ValueError):without_monte(x)


if __name__=='__main__':unittest.main()
