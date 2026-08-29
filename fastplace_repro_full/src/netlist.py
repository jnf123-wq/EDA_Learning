from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Cell:
    id: str
    w: float
    h: float
    x: float = 0.0
    y: float = 0.0
    fixed: bool = False


@dataclass
class Net:
    id: str
    pins: List[str] = field(default_factory=list)


@dataclass
class Netlist:
    board_w: float
    board_h: float
    cells: Dict[str, Cell] = field(default_factory=dict)
    nets: List[Net] = field(default_factory=list)

    def cell_ids(self) -> List[str]:
        return list(self.cells.keys())

    def movable_cells(self) -> List[Cell]:
        return [c for c in self.cells.values() if not c.fixed]

    def fixed_cells(self) -> List[Cell]:
        return [c for c in self.cells.values() if c.fixed]


def load_netlist(path: str) -> Netlist:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    nl = Netlist(board_w=float(d["board"]["width"]), board_h=float(d["board"]["height"]))

    for c in d["cells"]:
        cell = Cell(
            id=c["id"],
            w=float(c["w"]),
            h=float(c["h"]),
            x=float(c.get("x", 0.0)),
            y=float(c.get("y", 0.0)),
            fixed=bool(c.get("fixed", False)),
        )
        nl.cells[cell.id] = cell

    for n in d["nets"]:
        nl.nets.append(Net(id=n["id"], pins=list(n["pins"])))

    return nl
