import unittest
import numpy as np
from hydro_hourly_forecast import epoch
from hydro_upstream_qc_experiment import masked_inputs


class InputQualityExperimentTests(unittest.TestCase):
    def setUp(self):
        self.t=epoch('2026-07-22T08:00:00-03:00')+np.arange(5)*900
        self.z={'times':self.t,'monte:Q':np.array([0.,0.,0.,0.,9907.]),'monte:I':np.array([0.,0.,9969.,9969.,9969.]),'raw:monte:Q':np.array([0.,0.,0.,0.,9907.]),'castro:Q':np.ones(5)*1205}
        self.policy={'windows':[{'key':'monte:Q','start':'2026-07-22T08:00:00-03:00','end_exclusive':'2026-07-22T09:00:00-03:00','expected_slots':4,'expected_value':0}]}

    def test_masks_only_audited_delayed_slots_and_preserves_original(self):
        result=masked_inputs(self.z,self.policy,'Q_missing')
        self.assertTrue(np.isnan(result['monte:Q'][:4]).all())
        self.assertEqual(result['monte:Q'][4],9907.)
        self.assertTrue((self.z['monte:Q'][:4]==0).all())
        for key in ['times','monte:I','raw:monte:Q','castro:Q']:
            np.testing.assert_array_equal(result[key],self.z[key])

    def test_policy_rejects_revised_values_or_different_grid(self):
        self.z['monte:Q'][0]=10.
        with self.assertRaises(ValueError):masked_inputs(self.z,self.policy,'Q_missing')
        self.z['monte:Q'][0]=0.;self.policy['windows'][0]['expected_slots']=5
        with self.assertRaises(ValueError):masked_inputs(self.z,self.policy,'Q_missing')


if __name__=='__main__':unittest.main()
