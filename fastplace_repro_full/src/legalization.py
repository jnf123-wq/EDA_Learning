# -*- coding: utf-8 -*-
"""Stage 3a: Legalization（合法化）.

FastPlace 的全局布局结束后仍可能存在重叠。详细布局（Detailed Placement）
通常要求一个无重叠的合法布局作为输入，因此本复现增加一个简单的
"网格贪心合法化"步骤：把每个可动器件吸附到距离原位置最近的空闲 bin 槽，
并标记该器件覆盖的所有 bin，从而保证零重叠。

说明：这是教学级实现，等价于论文流程里"布局合法化"的简化版；
FastPlace 原文对标准单元采用按行（row）的合法化，这里针对矩形块
（更接近功率 PCB 元件）改为二维 bin 网格。
"""

from __future__ import annotations

import numpy as np


def _overlaps(a, b):
    dx = min(a.x + a.w / 2, b.x + b.w / 2) - max(a.x - a.w / 2, b.x - b.w / 2)
    dy = min(a.y + a.h / 2, b.y + b.h / 2) - max(a.y - a.h / 2, b.y - b.h / 2)
    return dx > 1e-9 and dy > 1e-9


def _inside(cell, board_w, board_h):
    return (
        cell.x - cell.w / 2 >= -1e-9
        and cell.x + cell.w / 2 <= board_w + 1e-9
        and cell.y - cell.h / 2 >= -1e-9
        and cell.y + cell.h / 2 <= board_h + 1e-9
    )


def is_legal(netlist):
    """布局是否合法：所有器件都在板内，且两两互不重叠。"""
    cells = list(netlist.cells.values())
    for c in cells:
        if not _inside(c, netlist.board_w, netlist.board_h):
            return False
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            if _overlaps(cells[i], cells[j]):
                return False
    return True


def _bin_range(lo, hi, board_len, n):
    bw = board_len / n
    i0 = int(lo / bw)
    i1 = int((hi - 1e-9) / bw)
    i0 = max(0, min(n - 1, i0))
    i1 = max(0, min(n - 1, i1))
    return i0, i1


def legalize(netlist, bin_w=2.0, bin_h=2.0):
    """网格贪心合法化，直接原地修改 netlist 中的可动器件坐标。"""
    board_w, board_h = netlist.board_w, netlist.board_h
    nx = max(1, int(np.ceil(board_w / bin_w)))
    ny = max(1, int(np.ceil(board_h / bin_h)))
    bw = board_w / nx
    bh = board_h / ny

    # 占用网格：固定器件先占据它们覆盖的 bin
    occ = np.zeros((nx, ny), dtype=bool)
    for c in netlist.cells.values():
        if c.fixed:
            i0, i1 = _bin_range(c.x - c.w / 2, c.x + c.w / 2, board_w, nx)
            j0, j1 = _bin_range(c.y - c.h / 2, c.y + c.h / 2, board_h, ny)
            occ[i0:i1 + 1, j0:j1 + 1] = True

    movable = sorted(
        (c for c in netlist.cells.values() if not c.fixed),
        key=lambda c: (c.x, c.y),
    )

    for c in movable:
        best = None
        best_cost = float("inf")
        for i in range(nx):
            for j in range(ny):
                cx = (i + 0.5) * bw
                cy = (j + 0.5) * bh
                # 器件必须完整落在板内
                if cx - c.w / 2 < -1e-9 or cx + c.w / 2 > board_w + 1e-9:
                    continue
                if cy - c.h / 2 < -1e-9 or cy + c.h / 2 > board_h + 1e-9:
                    continue
                i0, i1 = _bin_range(cx - c.w / 2, cx + c.w / 2, board_w, nx)
                j0, j1 = _bin_range(cy - c.h / 2, cy + c.h / 2, board_h, ny)
                if occ[i0:i1 + 1, j0:j1 + 1].any():
                    continue
                # 选择离原位置最近的槽，尽量保持全局布局结构
                cost = (cx - c.x) ** 2 + (cy - c.y) ** 2
                if cost < best_cost:
                    best_cost = cost
                    best = (i0, i1, j0, j1, cx, cy)

        if best is None:
            raise RuntimeError(f"legalize: no free slot for cell {c.id}")

        i0, i1, j0, j1, cx, cy = best
        occ[i0:i1 + 1, j0:j1 + 1] = True
        c.x, c.y = cx, cy

    return netlist
