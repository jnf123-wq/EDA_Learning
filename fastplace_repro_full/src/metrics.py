import numpy as np


def cell_pos_dict(netlist):
    return {c.id: (c.x, c.y) for c in netlist.cells.values()}


def net_hpwl(netlist, pos):
    """半周长线长（HPWL），pos: cell_id -> (x, y)。"""
    total = 0.0
    for net in netlist.nets:
        xs = [pos[c][0] for c in net.pins if c in pos]
        ys = [pos[c][1] for c in net.pins if c in pos]
        if not xs:
            continue
        total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def overlap_area(a, b):
    """两个矩形（中心坐标 + 半宽/半高）的重叠面积。"""
    dx = min(a.x + a.w / 2, b.x + b.w / 2) - max(a.x - a.w / 2, b.x - b.w / 2)
    dy = min(a.y + a.h / 2, b.y + b.h / 2) - max(a.y - a.h / 2, b.y - b.h / 2)
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def total_overlap_area(netlist):
    cells = list(netlist.cells.values())
    ov = 0.0
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            ov += overlap_area(cells[i], cells[j])
    return ov


def total_cell_area(netlist):
    return sum(c.w * c.h for c in netlist.cells.values())


def overlap_ratio(netlist):
    return total_overlap_area(netlist) / max(total_cell_area(netlist), 1e-12)
