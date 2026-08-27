import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

import numpy as np

from netlist import Cell, Net, Netlist
from netmodel import build_system
from qpsolver import solve


class TestQPSolver(unittest.TestCase):
    def test_midpoint(self):
        nl = Netlist(100, 100)
        nl.cells["a"] = Cell("a", 1, 1, x=0, y=0, fixed=True)
        nl.cells["b"] = Cell("b", 1, 1, x=10, y=0, fixed=True)
        nl.cells["m"] = Cell("m", 1, 1)
        nl.nets = [Net("n1", ["m", "a"]), Net("n2", ["m", "b"])]

        Q, dx, dy, id2i, dummy = build_system(nl)
        N = Q.shape[0]
        fixed_mask = np.zeros(N, dtype=bool)
        fixed_xy = np.zeros((N, 2))
        for c in nl.cells.values():
            i = id2i[c.id]
            if c.fixed:
                fixed_mask[i] = True
                fixed_xy[i] = (c.x, c.y)

        pos = solve(Q, dx, dy, fixed_mask, fixed_xy)
        m = id2i["m"]
        self.assertAlmostEqual(pos[m, 0], 5.0, places=8)
        self.assertAlmostEqual(pos[m, 1], 0.0, places=8)


if __name__ == "__main__":
    unittest.main()
