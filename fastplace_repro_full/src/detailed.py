# -*- coding: utf-8 -*-
"""Stage 3b: Detailed Placement（详细布局 / 精密布局）.

论文第三阶段是 Detailed Placement。它在已合法化的布局上，用 HPWL 作为
代价函数做两类低风险局部变换：

1. Cell Move（单器件移动）：把器件移到相邻合法位置，接受 HPWL 下降的移动。
2. Cell Swap（器件交换）：交换两个同尺寸器件，接受 HPWL 下降的交换。

同尺寸交换天然保持合法性，这与标准单元布局中"交换两个同宽标准单元"一致；
对矩形块布局（功率 PCB 元件），本实现仅交换宽高相同的器件，保证不引入新重叠。
"""

from __future__ import annotations

from metrics import net_hpwl
from legalization import is_legal


def _hpwl(netlist):
    return net_hpwl(netlist, {c.id: (c.x, c.y) for c in netlist.cells.values()})


def _try_move(netlist, cell, nx, ny):
    old = (cell.x, cell.y)
    cell.x, cell.y = nx, ny
    ok = is_legal(netlist)
    cell.x, cell.y = old
    return ok


def _cell_moves(netlist, step):
    cells = [c for c in netlist.cells.values() if not c.fixed]
    for cell in cells:
        best = (cell.x, cell.y)
        best_cost = _hpwl(netlist)
        for dxx in (-step, 0.0, step):
            for dyy in (-step, 0.0, step):
                if dxx == 0.0 and dyy == 0.0:
                    continue
                nx, ny = cell.x + dxx, cell.y + dyy
                if not _try_move(netlist, cell, nx, ny):
                    continue
                old = (cell.x, cell.y)
                cell.x, cell.y = nx, ny
                cost = _hpwl(netlist)
                cell.x, cell.y = old
                if cost < best_cost - 1e-12:
                    best_cost = cost
                    best = (nx, ny)
        cell.x, cell.y = best
    return netlist


def _cell_swaps(netlist):
    cells = [c for c in netlist.cells.values() if not c.fixed]
    base = _hpwl(netlist)
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            a, b = cells[i], cells[j]
            # 只交换同尺寸器件，保证交换后仍然合法
            if abs(a.w - b.w) > 1e-12 or abs(a.h - b.h) > 1e-12:
                continue
            ax, ay, bx, by = a.x, a.y, b.x, b.y
            a.x, a.y, b.x, b.y = bx, by, ax, ay
            if is_legal(netlist):
                cost = _hpwl(netlist)
                if cost < base - 1e-12:
                    base = cost
                    continue
            # 不改善则回退
            a.x, a.y, b.x, b.y = ax, ay, bx, by
    return netlist


def detailed_place(netlist, iterations=3, step=2.0):
    """详细布局：交替执行单器件移动与同尺寸器件交换。"""
    for _ in range(iterations):
        _cell_moves(netlist, step)
        _cell_swaps(netlist)
    return netlist
