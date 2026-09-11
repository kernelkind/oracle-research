import unittest
import numpy as np
from geometric_diffusion_readout import replay


class DiffusionReadoutTests(unittest.TestCase):
    def test_replay_retains_old_proximity_after_points_separate(self):
        snapshots = {0: np.array([[0.], [.1], [2.]]),
                     1: np.array([[0.], [1.9], [2.]])}
        result = replay(snapshots, .2)
        self.assertEqual(result[0]['groups'], [[0, 1], [2]])
        self.assertEqual(result[1]['groups'], [[0, 1, 2]])

    def test_threshold_does_not_change_observed_coordinates(self):
        x = np.array([[0.], [.1], [2.]])
        snapshots = {0: x.copy()}
        self.assertEqual(replay(snapshots, .05)[0]['groups'], [[0], [1], [2]])
        self.assertEqual(replay(snapshots, .2)[0]['groups'], [[0, 1], [2]])
        np.testing.assert_array_equal(snapshots[0], x)


if __name__ == '__main__':
    unittest.main()
