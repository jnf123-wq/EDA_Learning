import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

import numpy as np

from netlist import Cell, Net, Netlist
from netmodel import build_system


class TestNetModel(unittest.TestCase):
    def _make(self):
        nl = Netlist(100, 100)
        nl.cells["a"] = Cell("a", 4, 4, x=0, y=0)
        nl.cells["b"] = Cell("b", 4, 4, x=10, y=0, fixed=True)
        nl.cells["c"] = Cell("c", 4, 4, x=10, y=10, fixed=True)
        nl.nets = [Net("n1", ["a", "b"]), Net("n2", ["a", "c"])]
        return nl

    def test_symmetric_and_laplacian(self):
        nl = self._make()
        Q, dx, dy, id2i, dummy = build_system(nl)
        A = Q.toarray()
        self.assertTrue(np.allclose(A, A.T, atol=1e-12))
        self.assertTrue(np.allclose(A.sum(axis=1), 0.0, atol=1e-12))


if __name__ == "__main__":
    unittest.main()
