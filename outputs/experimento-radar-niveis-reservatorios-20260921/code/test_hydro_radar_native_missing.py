import unittest
import numpy as np

from hydro_radar_native_missing import training_masks


class NativeMissingTrainingTest(unittest.TestCase):
    def test_auxiliary_missing_changes_training_membership_without_changing_targets(self):
        t=np.arange(10,dtype=float)*3600
        base=np.ones(10);target=np.ones(10);complete=np.ones(10,dtype=bool)
        complete[2]=False;base[3]=np.nan;target[4]=np.nan
        masks=training_masks(t,base,target,complete,1,7*3600,10*3600)
        self.assertFalse(masks['validation','baseline'][2])
        self.assertTrue(masks['validation','candidate'][2])
        for mask in masks.values():
            self.assertFalse(mask[3]);self.assertFalse(mask[4])
        for phase in ('validation','test'):
            self.assertTrue(np.all(~masks[phase,'baseline']|masks[phase,'candidate']))

    def test_targets_at_cutoff_and_original_october_boundary_are_excluded(self):
        t=np.arange(12,dtype=float)*3600
        base=np.ones(12);target=np.ones(12);complete=np.ones(12,dtype=bool)
        masks=training_masks(t,base,target,complete,2,6*3600,11*3600)
        for family in ('baseline','candidate'):
            np.testing.assert_array_equal(np.flatnonzero(masks['validation',family]),[0,1,2,3])
            np.testing.assert_array_equal(np.flatnonzero(masks['test',family]),[0,1,2,3,6,7,8])
            self.assertFalse(masks['test',family][9])


if __name__=='__main__':unittest.main()
