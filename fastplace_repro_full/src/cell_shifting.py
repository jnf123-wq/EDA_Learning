"""FastPlace-style cell shifting (paper version).

Implements the cell-shifting procedure from the FastPlace paper:

  1. divide the placement region into a regular grid of bins;
  2. accumulate the total movable-cell area in every column (x direction)
     and every row (y direction);
  3. shift the column / row boundaries so that every column width and every
     row height is proportional to the cell area it contains;
  4. linearly map every movable cell onto the new boundaries to obtain its
     target position (this preserves the relative order of the cells);
  5. return the target of every movable cell together with a pseudo-pin
     weight.  The placer adds these targets as pseudo pins into the quadratic
     wirelength system, so the next QP solve trades off wirelength against
     spreading.

`compute_utilization` is kept for diagnostics and unit tests.
"""

import numpy as np


def build_bins(board_w, board_h, bin_w, bin_h):
    nx = max(1, int(np.ceil(board_w / bin_w)))
    ny = max(1, int(np.ceil(board_h / bin_h)))
    return nx, ny


def _bin_of(x, y, board_w, board_h, nx, ny):
    # i is the x-column index, j is the y-row index
    i = min(nx - 1, max(0, int(x / board_w * nx)))
    j = min(ny - 1, max(0, int(y / board_h * ny)))
    return i, j


def compute_utilization(netlist, bin_w, bin_h):
    """Return the (nx, ny) utilization matrix and the grid shape."""
    nx, ny = build_bins(netlist.board_w, netlist.board_h, bin_w, bin_h)
    util = np.zeros((nx, ny))
    bin_area = (netlist.board_w / nx) * (netlist.board_h / ny)
    for c in netlist.cells.values():
        i, j = _bin_of(c.x, c.y, netlist.board_w, netlist.board_h, nx, ny)
        util[i, j] += (c.w * c.h) / max(bin_area, 1e-12)
    return util, (nx, ny)


def _column_and_row_areas(netlist, nx, ny):
    """Total movable-cell area per column (x) and per row (y)."""
    col_area = np.zeros(nx)
    row_area = np.zeros(ny)
    for c in netlist.cells.values():
        if c.fixed:
            continue
        # column index is along x, row index is along y
        j = min(nx - 1, max(0, int(c.x / netlist.board_w * nx)))
        i = min(ny - 1, max(0, int(c.y / netlist.board_h * ny)))
        area = c.w * c.h
        col_area[j] += area
        row_area[i] += area
    return col_area, row_area


def shift_boundaries_1d(areas, total_len):
    """Return n+1 boundaries whose intervals are proportional to `areas`.

    A minimum interval width is enforced so that empty bins do not collapse
    to zero width and the boundary order stays strictly increasing.
    """
    areas = np.asarray(areas, dtype=float)
    n = areas.size
    if n == 0:
        return np.array([0.0, total_len])
    avg = total_len / n
    if areas.sum() <= 0:
        widths = np.full(n, avg)
    else:
        widths = areas / areas.sum() * total_len
        min_width = 0.15 * avg
        widths = np.maximum(widths, min_width)
        widths *= total_len / widths.sum()
    bounds = np.zeros(n + 1)
    bounds[1:] = np.cumsum(widths)
    bounds[-1] = total_len
    return bounds


def compute_targets(netlist, bin_w, bin_h):
    """Return {cell_id: (tx, ty)} targets for every movable cell.

    Each cell is linearly mapped inside its original column / row onto the
    shifted column / row boundaries.
    """
    nx, ny = build_bins(netlist.board_w, netlist.board_h, bin_w, bin_h)
    col_area, row_area = _column_and_row_areas(netlist, nx, ny)

    old_x = np.linspace(0.0, netlist.board_w, nx + 1)
    old_y = np.linspace(0.0, netlist.board_h, ny + 1)
    new_x = shift_boundaries_1d(col_area, netlist.board_w)
    new_y = shift_boundaries_1d(row_area, netlist.board_h)

    targets = {}
    for c in netlist.cells.values():
        if c.fixed:
            continue
        j = min(nx - 1, max(0, int(c.x / netlist.board_w * nx)))
        i = min(ny - 1, max(0, int(c.y / netlist.board_h * ny)))
        rx = (c.x - old_x[j]) / max(old_x[j + 1] - old_x[j], 1e-12)
        ry = (c.y - old_y[i]) / max(old_y[i + 1] - old_y[i], 1e-12)
        rx = min(1.0, max(0.0, rx))
        ry = min(1.0, max(0.0, ry))
        tx = new_x[j] + rx * (new_x[j + 1] - new_x[j])
        ty = new_y[i] + ry * (new_y[i + 1] - new_y[i])
        targets[c.id] = (float(tx), float(ty))
    return targets


def compute_anchors(netlist, bin_w, bin_h, target_util=0.7, spread_weight=0.6,
                    beta=None):
    """Paper-version cell shifting expressed as pseudo-pin anchors.

    Returns ``[(cell_id, tx, ty, weight), ...]`` for every movable cell,
    where ``weight`` is the pseudo-pin weight (beta).  ``target_util`` is kept
    only for backward compatibility and is unused by the paper version.
    """
    w = spread_weight if beta is None else beta
    targets = compute_targets(netlist, bin_w, bin_h)
    return [(cid, tx, ty, w) for cid, (tx, ty) in targets.items()]