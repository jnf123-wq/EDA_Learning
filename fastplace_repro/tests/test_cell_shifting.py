import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from netlist import Cell, Netlist
from cell_shifting import compute_anchors


class TestCellShifting(unittest.TestCase):
    def test_dense_bin_gives_anchors(self):
        nl = Netlist(100, 100)
        for k in range(9):
            c = Cell(f"c{k}", 5, 5, x=5.0, y=5.0)
            nl.cells[c.id] = c
        anchors = compute_anchors(nl, 10, 10, target_util=0.8, spread_weight=0.6)
        self.assertTrue(len(anchors) > 0)

    def test_uniform_bins_no_anchors(self):
        nl = Netlist(100, 100)
        pts = [(5, 5), (15, 5), (5, 15), (15, 15)]
        for k, (x, y) in enumerate(pts):
            c = Cell(f"c{k}", 5, 5, x=x, y=y)
            nl.cells[c.id] = c
        anchors = compute_anchors(nl, 10, 10, target_util=0.8, spread_weight=0.6)
        self.assertEqual(len(anchors), 0)


if __name__ == "__main__":
    unittest.main()
