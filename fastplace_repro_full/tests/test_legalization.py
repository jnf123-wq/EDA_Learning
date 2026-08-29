import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from netlist import Cell, Netlist
from legalization import legalize, is_legal
from metrics import total_overlap_area


class TestLegalization(unittest.TestCase):
    def test_removes_overlap(self):
        nl = Netlist(100, 100)
        for k in range(12):
            c = Cell(f"c{k}", 6, 4, x=5.0, y=5.0)
            nl.cells[c.id] = c
        legalize(nl, bin_w=2.0, bin_h=2.0)
        self.assertTrue(is_legal(nl))
        self.assertAlmostEqual(total_overlap_area(nl), 0.0, places=9)

    def test_respects_fixed_obstacles(self):
        nl = Netlist(100, 100)
        nl.cells["f"] = Cell("f", 2, 2, x=1.0, y=1.0, fixed=True)
        nl.cells["c"] = Cell("c", 2, 2, x=1.0, y=1.0)
        legalize(nl, bin_w=2.0, bin_h=2.0)
        self.assertTrue(is_legal(nl))


if __name__ == "__main__":
    unittest.main()
