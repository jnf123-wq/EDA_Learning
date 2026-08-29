import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from netlist import Cell, Net, Netlist
from refinement import local_refine
from metrics import net_hpwl


def hpwl(nl):
    return net_hpwl(nl, {c.id: (c.x, c.y) for c in nl.cells.values()})


class TestRefinement(unittest.TestCase):
    def test_hpwl_not_increase(self):
        nl = Netlist(100, 100)
        nl.cells["a"] = Cell("a", 4, 4, x=0, y=0, fixed=True)
        nl.cells["b"] = Cell("b", 4, 4, x=10, y=0)
        nl.nets = [Net("n1", ["a", "b"])]

        before = hpwl(nl)
        local_refine(nl, iterations=2, step=2.0)
        after = hpwl(nl)

        self.assertLessEqual(after, before + 1e-9)


if __name__ == "__main__":
    unittest.main()
