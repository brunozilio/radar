import unittest
import numpy as np
from hydro_component_fallback import component_conflict,source_dependencies,choose_forecast


class ComponentFallbackTest(unittest.TestCase):
    def test_missing_is_unknown_and_unrelated_components_are_not_double_counted(self):
        r=dict(val_vazaodefluente=0,val_vazaoturbinada=0,val_vazaovertida=0,val_vazaooutrasestruturas=6)
        self.assertTrue(component_conflict(r))
        for value in ('',None,'nan','inf'):
            self.assertFalse(component_conflict({**r,'val_vazaooutrasestruturas':value}))
        self.assertFalse(component_conflict({**r,'val_vazaodefluente':6}))
        self.assertFalse(component_conflict({**r,'val_vazaooutrasestruturas':1,'val_vazaovertidanaoturbinavel':9999}))

    def test_future_records_cannot_flag_past_origins(self):
        times=np.arange(12)*3600.;flags=np.zeros(12,dtype=bool);flags[4]=True
        origins=np.array([4,5,6,8,11])*3600.
        impact,used=source_dependencies(times,flags,origins)
        np.testing.assert_equal(impact.any(axis=1),[False,True,True,True,True])
        altered=flags.copy();altered[5:]=True
        a,_=source_dependencies(times,altered,origins[:2]);np.testing.assert_equal(a,impact[:2])
        self.assertTrue(np.all(used[np.isfinite(used)]<=np.repeat(origins,4).reshape(-1,4)[np.isfinite(used)]-3600))

    def test_expired_and_pre_series_records_cannot_be_used(self):
        flags,used=source_dependencies(np.array([3600.]),[True],np.array([0.,7200.,12600.,12601.]))
        self.assertFalse(flags[0].any());self.assertTrue(flags[1,0]);self.assertTrue(flags[2,0]);self.assertFalse(flags[3,0])
        with self.assertRaises(ValueError):source_dependencies([1,1],[True,True],[10])

    def test_branch_preserves_exact_baseline_without_conflict(self):
        self.assertEqual(choose_forecast('1.234567890','99',False),'1.234567890')
        self.assertEqual(choose_forecast('1.234567890','99',True),'99')


if __name__=='__main__':unittest.main()
