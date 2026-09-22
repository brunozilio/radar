import unittest
import numpy as np
from hydro_weighted_centering import weighted_fit
from hydro_hourly_forecast import ridge_fit
from hydro_upstream_audit import predict_many


class WeightedCenteringTests(unittest.TestCase):
    def test_matches_independent_augmented_fit_with_free_intercept(self):
        rng=np.random.default_rng(7);X=rng.normal(size=(100,4));X[::9,2]=np.nan
        y=10+np.nan_to_num(X)@np.array([2.,-1.,3.,4.]);w=1+2*(y>12);tr=np.arange(80);alpha=17.
        m=weighted_fit(X,y,tr,alpha,w)
        filled=np.column_stack([np.where(np.isfinite(X),X,m['median']),~np.isfinite(X)])
        mean=filled[tr].mean(axis=0);xx=(filled-mean)/m['scale'];design=np.column_stack([xx,np.ones(len(xx))])
        sw=np.sqrt(w[tr]/w[tr].mean())
        penalty=np.column_stack([np.sqrt(alpha)*np.eye(xx.shape[1]),np.zeros(xx.shape[1])])
        matrix=np.vstack([design[tr]*sw[:,None],penalty]);target=np.r_[y[tr]*sw,np.zeros(xx.shape[1])]
        coefficients=np.linalg.lstsq(matrix,target,rcond=None)[0]
        np.testing.assert_allclose(predict_many(m,X),design@coefficients,atol=1e-10)
        self.assertAlmostEqual(np.average(predict_many(m,X[tr])-y[tr],weights=w[tr]),0.,places=10)

    def test_uniform_weights_reproduce_reference(self):
        rng=np.random.default_rng(12);X=rng.normal(size=(50,3));y=rng.normal(size=50);tr=np.arange(40);w=np.ones(50)
        a=weighted_fit(X,y,tr,1000,w);b=ridge_fit(X,y,tr,1000,w)
        np.testing.assert_allclose(predict_many(a,X),predict_many(b,X),atol=1e-12)

    def test_future_data_cannot_change_training_transforms(self):
        rng=np.random.default_rng(5);X=rng.normal(size=(60,3));y=rng.normal(size=60);tr=np.arange(40);w=1+2*(y>0)
        a=weighted_fit(X,y,tr,1000,w);X[40:]=1e12;y[40:]=1e12;w[40:]=100
        b=weighted_fit(X,y,tr,1000,w)
        for k in a:np.testing.assert_allclose(a[k],b[k],atol=1e-12)
