import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

import numpy as np

from netlist import load_netlist
from placer import place
from legalization import is_legal
from metrics import total_overlap_area


class TestPlacer(unittest.TestCase):
    def test_end_to_end(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "toy.json")
        nl = load_netlist(path)
        initial_overlap = total_overlap_area(nl)

        cfg = {
            "max_iter": 12,
            "bin_w": 10.0,
            "bin_h": 10.0,
            "target_util": 0.7,
            "spread_weight": 0.6,
            "refine_every": 2,
            "refine_iters": 2,
            "legal_bin_w": 2.0,
            "legal_bin_h": 2.0,
            "detail_iters": 3,
            "detail_step": 2.0,
        }
        history = place(nl, cfg)

        self.assertGreaterEqual(len(history), cfg["max_iter"])
        for c in nl.cells.values():
            self.assertTrue(np.isfinite(c.x) and np.isfinite(c.y))
            self.assertGreaterEqual(c.x, -1e-6)
            self.assertLessEqual(c.x, nl.board_w + 1e-6)
            self.assertGreaterEqual(c.y, -1e-6)
            self.assertLessEqual(c.y, nl.board_h + 1e-6)

        self.assertTrue(is_legal(nl))
        self.assertAlmostEqual(total_overlap_area(nl), 0.0, places=9)
        self.assertLess(total_overlap_area(nl), initial_overlap)


if __name__ == "__main__":
    unittest.main()
