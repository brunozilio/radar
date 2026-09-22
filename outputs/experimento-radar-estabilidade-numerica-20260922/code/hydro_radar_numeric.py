"""Explicit research-only representation of observed RADAR rain features."""
import numpy as np

RAIN_START=45
FEATURE_COUNT=120
RAIN_DECIMALS=8

def normalize_observed_features(features):
    """Copy the120-column array; preserve levels/QI and all missingness exactly."""
    source=np.asarray(features,dtype=np.float64)
    if source.ndim!=2 or source.shape[1]!=FEATURE_COUNT:
        raise ValueError('Expected exactly120 observed feature columns')
    if np.isinf(source).any():
        raise ValueError('Infinite features are not part of the frozen source contract')
    result=source.copy()
    result[:,RAIN_START:]=np.round(source[:,RAIN_START:],decimals=RAIN_DECIMALS)
    rain=result[:,RAIN_START:]
    rain[rain==0]=0.0
    assert np.array_equal(np.isnan(result),np.isnan(source))
    np.testing.assert_array_equal(result[:,:RAIN_START],source[:,:RAIN_START])
    return result
