import unittest
import numpy as np
from hydro_upstream_2023_experiment import prepare_2023,numeric,PLANTS
from hydro_hourly_forecast import epoch


class HistoricalInputTests(unittest.TestCase):
    def rows(self,stamps):
        return [{'id_reservatorio':plant,'din_instante':stamp,'val_vazaodefluente':str(q),'val_vazaoafluente':str(i)} for plant in PLANTS.values() for stamp,q,i in stamps]

    def test_delay_prevents_future_input_and_missing_values_expire(self):
        times=epoch('2023-09-01T00:00:00-03:00')+np.arange(7)*3600
        rows=self.rows([('2023-09-01 01:00:00',100,90),('2023-09-01 05:00:00',500,490)])
        F,known,target,_=prepare_2023(rows,times)
        self.assertTrue(np.isnan(known[1]))
        np.testing.assert_allclose(known[[2,3,6]],[.1,.1,.5])
        self.assertTrue(np.isnan(known[4:6]).all())
        self.assertTrue(np.isnan(target[2:5]).all())
        changed=self.rows([('2023-09-01 01:00:00',100,90),('2023-09-01 05:00:00',99999,99999)])
        later=prepare_2023(changed,times)[0]
        np.testing.assert_allclose(F[:6],later[:6],equal_nan=True)

    def test_2359_can_be_delayed_input_but_never_invented_midnight_target(self):
        times=epoch('2023-09-02T00:00:00-03:00')+np.arange(2)*3600
        rows=self.rows([('2023-09-01 23:59:00',100,-10)])
        F,known,target,_=prepare_2023(rows,times)
        self.assertTrue(np.isnan(target).all())
        self.assertTrue(np.isnan(known[0]))
        self.assertEqual(known[1],.1)
        self.assertEqual(F[1,4],-.01)

    def test_nonfinite_and_negative_outflow_are_not_valid_but_signed_inflow_is(self):
        self.assertTrue(np.isnan(numeric('-1')))
        self.assertTrue(np.isnan(numeric('inf',True)))
        self.assertEqual(numeric('-1',True),-1)
        self.assertEqual(numeric('0'),0)
        self.assertEqual(numeric('9999'),9999)

    def test_duplicate_source_rows_cannot_silently_overwrite(self):
        rows=self.rows([('2023-09-01 01:00:00',100,90)]);rows.append(rows[0].copy())
        with self.assertRaises(ValueError):prepare_2023(rows,np.array([epoch('2023-09-01T02:00:00-03:00')]))
