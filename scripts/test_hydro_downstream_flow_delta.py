import unittest
import numpy as np
from hydro_downstream_flow_delta import stage,updated_stage,future_flow_delta,evaluate

class DownstreamDeltaTest(unittest.TestCase):
    def test_matches_direct_nonlinear_stage_with_common_anchor(self):
        rating=[4.6,.625,.39];anchor_q=1000.;anchor_h=6.1
        offset=anchor_h-float(stage(anchor_q,rating))
        for q in [0.,17.,1000.,14000.]:
            base=float(stage(q,rating))+offset
            unchanged,recovered,_=updated_stage(base,anchor_h,anchor_q,0.,rating)
            self.assertAlmostEqual(unchanged,base,places=11)
            self.assertAlmostEqual(recovered,q,places=8)
            for delta in [50.,-10.,3000.]:
                got,_,qnew=updated_stage(base,anchor_h,anchor_q,delta,rating)
                if q+delta<0:self.assertTrue(np.isnan(got))
                else:self.assertAlmostEqual(got,float(stage(q+delta,rating))+offset,places=10)
                self.assertAlmostEqual(qnew,q+delta,places=8)

    def test_future_lead_zero_enters_first_horizon_and_unused_future_is_ignored(self):
        self.assertEqual(future_flow_delta([100.,np.nan],[120.,np.nan],[.25,.75],[1,2],1),5.)
        self.assertTrue(np.isnan(future_flow_delta([100.,np.nan],[120.,np.nan],[.25,.75],[1,2],2)))
        with self.assertRaises(ValueError):future_flow_delta([100.],[120.],[1.],[0],1)

    def test_missing_anchor_and_below_rating_domain_are_not_filled(self):
        self.assertTrue(np.isnan(updated_stage(5.,np.nan,100.,20.,[4.6,.625,.39])[0]))
        with self.assertRaises(ValueError):updated_stage(-5.,5.,100.,20.,[4.6,.625,.39])

    def test_new_failure_stays_in_denominator_and_reference_still_scored(self):
        data=[dict(nominal_lead_h=12,actual_m=8.,julho_levels_m=8.1,julho_levels_rain_m=None)]
        result=[r for r in evaluate(data) if r['nominal_lead_h']==12 and r['subset']=='level_ge_7m' and r['population']=='all_available']
        self.assertEqual([r['paired_n'] for r in result],[1,0])
        self.assertEqual([r['observed_targets'] for r in result],[1,1])
        self.assertEqual(result[1]['forecast_failures_with_truth'],1)

if __name__=='__main__':unittest.main()
