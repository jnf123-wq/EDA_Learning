import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

import numpy as np

from netlist import Cell, Netlist
from cell_shifting import compute_anchors, compute_targets, shift_boundaries_1d


class TestShiftBoundaries(unittest.TestCase):
    def test_uniform_areas_keep_uniform(self):
        bounds = shift_boundaries_1d([1, 1, 1, 1], 100.0)
        self.assertEqual(len(bounds), 5)
        np.testing.assert_allclose(bounds, [0, 25, 50, 75, 100], atol=1e-9)

    def test_total_length_preserved(self):
        bounds = shift_boundaries_1d([0, 10, 0, 5], 80.0)
        self.assertAlmostEqual(bounds[0], 0.0)
        self.assertAlmostEqual(bounds[-1], 80.0)

    def test_zero_areas_do_not_collapse(self):
        bounds = shift_boundaries_1d([0, 0, 0], 30.0)
        self.assertTrue(np.all(np.diff(bounds) > 0))


class TestCellShiftingPaper(unittest.TestCase):
    def test_targets_for_every_movable_cell(self):
        nl = Netlist(100, 100)
        for k in range(9):
            c = Cell("c%d" % k, 5, 5, x=5.0, y=5.0)
            nl.cells[c.id] = c
        targets = compute_targets(nl, 10, 10)
        self.assertEqual(len(targets), 9)
        for tx, ty in targets.values():
            self.assertGreaterEqual(tx, 0.0)
            self.assertLessEqual(tx, 100.0)
            self.assertGreaterEqual(ty, 0.0)
            self.assertLessEqual(ty, 100.0)

    def test_dense_cells_are_spread(self):
        nl = Netlist(100, 100)
        for k in range(4):
            c = Cell("c%d" % k, 5, 5, x=5.0, y=15.0 + 20 * k)
            nl.cells[c.id] = c
        targets = compute_targets(nl, 10, 10)
        xs = [t for t, _ in targets.values()]
        self.assertTrue(all(t > 5.0 for t in xs))

    def test_order_preserved_along_x(self):
        nl = Netlist(100, 100)
        cells = []
        for k, x in enumerate([5.0, 15.0, 25.0, 35.0]):
            c = Cell("c%d" % k, 5, 5, x=x, y=50.0)
            nl.cells[c.id] = c
            cells.append(c)
        targets = compute_targets(nl, 10, 10)
        tx = [targets[c.id][0] for c in cells]
        self.assertTrue(all(tx[i] < tx[i + 1] for i in range(len(tx) - 1)))

    def test_fixed_cells_excluded(self):
        nl = Netlist(100, 100)
        c1 = Cell("c1", 5, 5, x=5.0, y=5.0)
        c2 = Cell("c2", 5, 5, x=15.0, y=15.0, fixed=True)
        nl.cells[c1.id] = c1
        nl.cells[c2.id] = c2
        targets = compute_targets(nl, 10, 10)
        self.assertIn("c1", targets)
        self.assertNotIn("c2", targets)

    def test_compute_anchors_uses_beta(self):
        nl = Netlist(100, 100)
        for k in range(3):
            c = Cell("c%d" % k, 5, 5, x=5.0, y=5.0)
            nl.cells[c.id] = c
        anchors = compute_anchors(nl, 10, 10, beta=0.9)
        self.assertEqual(len(anchors), 3)
        for cid, tx, ty, w in anchors:
            self.assertAlmostEqual(w, 0.9)


if __name__ == "__main__":
    unittest.main()