import numpy as np


def build_bins(board_w, board_h, bin_w, bin_h):
    nx = max(1, int(np.ceil(board_w / bin_w)))
    ny = max(1, int(np.ceil(board_h / bin_h)))
    return nx, ny


def _bin_of(x, y, board_w, board_h, nx, ny):
    i = min(nx - 1, max(0, int(x / board_w * nx)))
    j = min(ny - 1, max(0, int(y / board_h * ny)))
    return i, j


def compute_utilization(netlist, bin_w, bin_h):
    nx, ny = build_bins(netlist.board_w, netlist.board_h, bin_w, bin_h)
    util = np.zeros((nx, ny))
    bin_area = (netlist.board_w / nx) * (netlist.board_h / ny)
    for c in netlist.cells.values():
        i, j = _bin_of(c.x, c.y, netlist.board_w, netlist.board_h, nx, ny)
        util[i, j] += (c.w * c.h) / max(bin_area, 1e-12)
    return util, (nx, ny)


def compute_anchors(netlist, bin_w, bin_h, target_util=0.7, spread_weight=0.6):
    """对过密 bin 里的可动器件，生成指向稀疏 bin 中心的伪锚点。"""
    util, (nx, ny) = compute_utilization(netlist, bin_w, bin_h)
    over = [(i, j) for i in range(nx) for j in range(ny) if util[i, j] > target_util]
    under = [(i, j) for i in range(nx) for j in range(ny) if util[i, j] < target_util * 0.5]
    if not over or not under:
        return []

    anchors = []
    for c in netlist.cells.values():
        if c.fixed:
            continue
        i, j = _bin_of(c.x, c.y, netlist.board_w, netlist.board_h, nx, ny)
        if util[i, j] > target_util:
            bi, bj = min(under, key=lambda b: (b[0] - i) ** 2 + (b[1] - j) ** 2)
            cx = (bi + 0.5) * netlist.board_w / nx
            cy = (bj + 0.5) * netlist.board_h / ny
            anchors.append((c.id, cx, cy, spread_weight))
    return anchors
