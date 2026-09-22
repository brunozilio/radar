import unittest
import tempfile
from pathlib import Path
import numpy as np
from hydro_upstream_tree_experiment import partitions,same_time_observation
from hydro_hourly_forecast import epoch

class ChronologicalExperimentTests(unittest.TestCase):
    def test_finite_asof_value_is_not_a_same_time_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);origin=epoch('2026-09-21T17:00:00-03:00')
            z={'raw:julho:Q':np.array([5000.])}
            for stamp,expected in [('16:00',False),('17:00',True)]:
                (path/'idades-fontes.csv').write_text('source,last_time\njulho,2026-09-21T'+stamp+':00-03:00\n')
                result=same_time_observation(path,z,'julho:Q',origin)
                self.assertEqual(np.isfinite(result),expected)
                if expected:self.assertEqual(result,5.)

    def test_future_target_cannot_cross_training_boundaries(self):
        boundaries=[epoch(t+'T00:00:00-03:00') for t in ['2025-10-01','2026-07-01','2026-09-21']]
        times=np.array(sorted({b+delta*3600 for b in boundaries for delta in range(-15,16)}))
        target=np.ones(len(times));known=np.ones(len(times))
        for lead in [0,1,6,11]:
            indexes=partitions(times,target,known,lead)
            for key,cutoff in zip(['train','pretest','final'],boundaries):
                self.assertTrue(np.all(times[indexes[key]]+lead*3600<cutoff))
                boundary_row=np.where(times+lead*3600==cutoff)[0]
                self.assertFalse(set(boundary_row)&set(indexes[key]))
            self.assertFalse(set(indexes['train'])&set(indexes['validation']))
            self.assertFalse(set(indexes['pretest'])&set(indexes['test']))

    def test_unknown_targets_and_unknown_reference_are_never_filled_for_training(self):
        times=np.array([epoch('2025-09-01T00:00:00-03:00')+i*3600 for i in range(4)])
        indexes=partitions(times,np.array([1.,np.nan,2.,3.]),np.array([1.,1.,np.nan,2.]),1)
        np.testing.assert_array_equal(indexes['train'],[0,3])

if __name__=='__main__':unittest.main()
