import unittest
from unittest.mock import patch
import numpy as np
from hydro_nonnegative_upstream import positive_ridge_fit
from hydro_upstream_audit import predict_many
from hydro_hourly_forecast import ridge_fit
import hydro_nonnegative_upstream as subject


class NonnegativeRidgeTests(unittest.TestCase):
    def test_unused_upper_factor_storage_cannot_change_objective(self):
        rng=np.random.default_rng(57);x=rng.normal(size=(200,53));y=x[:,0]*3-x[:,1]*2
        train=np.arange(180);w=np.ones(200);factor=subject.cholesky
        def dirty(*args,**kwargs):
            f=factor(*args,**kwargs)
            f[np.triu_indices(len(f),1)]=1e12
            return f
        with patch.object(subject,'cholesky',side_effect=dirty):
            model,diag=positive_ridge_fit(x,y,train,1000,w)
        self.assertLess(diag['kkt_relative'],1e-7)
        self.assertTrue(np.all(model['beta'][:53]>=-1e-9))

    def test_negative_response_cannot_create_negative_flow_coefficient(self):
        x=np.arange(30,dtype=float)[:,None];y=50-x[:,0];tr=np.arange(25);w=np.ones(30)
        baseline=ridge_fit(x,y,tr,10,w);model,diag=positive_ridge_fit(x,y,tr,10,w)
        self.assertLess(baseline['beta'][0],0)
        self.assertGreaterEqual(model['beta'][0],-1e-10)
        self.assertTrue(diag['success'])
        p=predict_many(model,np.array([[20.],[40.]]))
        self.assertGreaterEqual(p[1],p[0]-1e-10)

    def test_training_transform_never_uses_future_outlier(self):
        rng=np.random.default_rng(7);x=rng.normal(size=(60,3));x[2,1]=np.nan
        y=np.nan_to_num(x)@np.array([1.,2.,3.]);w=np.ones(60);tr=np.arange(40)
        a,_=positive_ridge_fit(x,y,tr,1000,w)
        x[40:]=1e12;y[40:]=-1e12
        b,_=positive_ridge_fit(x,y,tr,1000,w)
        for k in a:np.testing.assert_allclose(a[k],b[k],atol=1e-12)

    def test_free_missing_indicator_preserves_solver_feasibility(self):
        x=np.arange(50,dtype=float)[:,None];x[::2]=np.nan
        y=np.where(np.isnan(x[:,0]),-10.,np.nan_to_num(x[:,0]));w=np.ones(50)
        model,diag=positive_ridge_fit(x,y,np.arange(50),1,w)
        self.assertTrue(diag['success'])
        self.assertGreaterEqual(model['beta'][0],0)
        self.assertLess(model['beta'][1],0)
