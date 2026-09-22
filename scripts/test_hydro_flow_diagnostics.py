import unittest
import numpy as np
from hydro_flow_diagnostics import attribution,outside_training_range,feature_names
from hydro_hourly_forecast import ridge_fit,ridge_predict

class FlowDiagnosticsTest(unittest.TestCase):
    def test_contributions_reconstruct_prediction_including_missing_indicators(self):
        rng=np.random.default_rng(9);X=rng.normal(size=(100,3));X[::3,1]=np.nan
        y=2*X[:,0]+np.nan_to_num(X[:,1]);state=ridge_fit(X,y,np.arange(100),10,np.ones(100))
        current=np.array([12,np.nan,-2])
        values=attribution(state,current,['a','b','c'])
        self.assertEqual(len(values),6)
        self.assertAlmostEqual(sum(v['contribution_m3_s'] for v in values)/1000+state['intercept'],ridge_predict(state,current),places=12)

    def test_bounds_are_training_only_and_missing_is_not_an_extreme(self):
        training=np.array([[1,2,np.nan],[2,np.nan,np.nan],[3,4,np.nan]])
        result=outside_training_range(training,np.array([4,np.nan,100]),['a','b','c'])
        self.assertEqual(result,[{'feature':'a','current_value':4.,'training_min':1.,'training_max':3.}])
        self.assertEqual(outside_training_range(training,np.array([3,2,np.nan]),['a','b','c']),[])

    def test_feature_schema_is_unambiguous(self):
        names=feature_names();self.assertEqual(len(names),53);self.assertEqual(len(set(names)),53)

if __name__=='__main__':unittest.main()
