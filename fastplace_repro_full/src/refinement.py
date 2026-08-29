from metrics import net_hpwl


def _hpwl(netlist):
    pos = {c.id: (c.x, c.y) for c in netlist.cells.values()}
    return net_hpwl(netlist, pos)


def _legal(netlist, cell, nx, ny):
    if nx - cell.w / 2 < 0 or nx + cell.w / 2 > netlist.board_w:
        return False
    if ny - cell.h / 2 < 0 or ny + cell.h / 2 > netlist.board_h:
        return False
    for c in netlist.cells.values():
        if c.id == cell.id:
            continue
        if abs(nx - c.x) < (cell.w + c.w) / 2 - 1e-9 and abs(ny - c.y) < (cell.h + c.h) / 2 - 1e-9:
            return False
    return True


def local_refine(netlist, iterations=2, step=2.0):
    """FastPlace 的 iterative local refinement：用 HPWL 在相邻位置做局部搜索。"""
    cells = list(netlist.cells.values())
    for _ in range(iterations):
        for cell in cells:
            if cell.fixed:
                continue
            cur = _hpwl(netlist)
            best_x, best_y = cell.x, cell.y
            best_cost = cur
            for dxx in (-step, 0.0, step):
                for dyy in (-step, 0.0, step):
                    if dxx == 0.0 and dyy == 0.0:
                        continue
                    nx, ny = cell.x + dxx, cell.y + dyy
                    if not _legal(netlist, cell, nx, ny):
                        continue
                    old = (cell.x, cell.y)
                    cell.x, cell.y = nx, ny
                    cost = _hpwl(netlist)
                    cell.x, cell.y = old
                    if cost < best_cost - 1e-12:
                        best_cost = cost
                        best_x, best_y = nx, ny
            cell.x, cell.y = best_x, best_y
    return netlist
