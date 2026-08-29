import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from netlist import Cell, Net, Netlist
from legalization import legalize, is_legal
from detailed import detailed_place
from metrics import net_hpwl


def hpwl(nl):
    return net_hpwl(nl, {c.id: (c.x, c.y) for c in nl.cells.values()})


class TestDetailed(unittest.TestCase):
    def test_no_worse_and_legal(self):
        nl = Netlist(100, 100)
        nl.cells["a"] = Cell("a", 4, 4, x=2.0, y=50.0, fixed=True)
        nl.cells["b"] = Cell("b", 4, 4, x=98.0, y=50.0, fixed=True)
        nl.cells["m1"] = Cell("m1", 4, 4)
        nl.cells["m2"] = Cell("m2", 4, 4)
        nl.nets = [Net("n1", ["a", "m1"]), Net("n2", ["m1", "m2"]), Net("n3", ["m2", "b"])]

        legalize(nl, bin_w=2.0, bin_h=2.0)
        before = hpwl(nl)
        detailed_place(nl, iterations=3, step=2.0)
        after = hpwl(nl)

        self.assertLessEqual(after, before + 1e-9)
        self.assertTrue(is_legal(nl))


if __name__ == "__main__":
    unittest.main()
