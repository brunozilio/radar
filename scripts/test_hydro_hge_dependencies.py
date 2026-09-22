import unittest
import numpy as np
from hydro_hge_dependencies import routing_parts


class RoutingPartsTest(unittest.TestCase):
    def test_transition_keeps_origin_zero_as_prediction(self):
        # lead 1 with lags 1,2: origin is modeled; the older sample is historical.
        got = routing_parts(np.array([10., 20., 30.]), {0: 50.}, [.25, .75], [1, 2], 1, 40.)
        self.assertEqual(got, (15., 12.5, 10., .25))

    def test_all_future_and_missing_inputs(self):
        self.assertEqual(routing_parts([999.], {0: 10., 1: 20.}, [.5, .5], [1, 2], 2, 7.), (0., 15., 7., 1.))
        with self.assertRaises(ValueError):
            routing_parts([999.], {0: np.nan}, [1.], [1], 1, 7.)


if __name__ == '__main__':
    unittest.main()
