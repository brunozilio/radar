import unittest
import numpy as np
from hydro_future_flow_diagnostic import observed_delta

class FutureFlowDiagnosticTest(unittest.TestCase):
    def test_only_nonnegative_relative_lag_changes_and_exact_zero_is_skipped(self):
        self.assertEqual(observed_delta([10,20],[999,100,200],1,1,[1],[1]),(90.,1))
        self.assertEqual(observed_delta([],[],0,1,[1],[4]),(0.,0))
        self.assertEqual(observed_delta([10],[np.nan],0,1,[0,1],[1,4]),(0.,0))

    def test_required_missing_truth_never_falls_back_to_estimate(self):
        v,n=observed_delta([10],[np.nan],0,1,[1],[1])
        self.assertTrue(np.isnan(v));self.assertEqual(n,1)

    def test_history_and_later_truth_cannot_change_selected_future_terms(self):
        a=np.arange(20,dtype=float);b=a.copy();b[:5]=999;b[7:]=999
        x=observed_delta([1,2],a,5,2,[.25,.75],[1,2])
        self.assertEqual(x,observed_delta([1,2],b,5,2,[.25,.75],[1,2]))
        with self.assertRaises(ValueError):observed_delta([1],a,5,1,[1],[0])

if __name__=='__main__':unittest.main()
