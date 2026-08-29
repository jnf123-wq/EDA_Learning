# -*- coding: utf-8 -*-
"""FastPlace 复现主流程。

完整三阶段：
  Stage 1: Global Optimization（二次线长 + cell shifting）
  Stage 2: Iterative Local Refinement（HPWL 局部精化，与 Stage 1 交错）
  Stage 3: Legalization + Detailed Placement（合法化 + 详细布局）
"""

import numpy as np

from netmodel import build_system
from qpsolver import solve
from cell_shifting import compute_anchors
from refinement import local_refine
from legalization import legalize
from detailed import detailed_place
from metrics import net_hpwl, total_overlap_area


def _pos(netlist):
    return {c.id: (c.x, c.y) for c in netlist.cells.values()}


def place(netlist, cfg):
    history = []
    anchors = {}

    max_iter = int(cfg["max_iter"])

    # ---- Stage 1 & 2：全局布局 + cell shifting + 交错式局部精化 ----
    for it in range(max_iter):
        Q, dx, dy, id_to_idx, dummy_idx = build_system(netlist, list(anchors.values()))
        N = Q.shape[0]

        fixed_mask = np.zeros(N, dtype=bool)
        fixed_xy = np.zeros((N, 2))
        for c in netlist.cells.values():
            i = id_to_idx[c.id]
            if c.fixed:
                fixed_mask[i] = True
                fixed_xy[i] = (c.x, c.y)

        pos = solve(Q, dx, dy, fixed_mask, fixed_xy)

        for c in netlist.cells.values():
            c.x = float(pos[id_to_idx[c.id], 0])
            c.y = float(pos[id_to_idx[c.id], 1])

        if it % int(cfg["refine_every"]) == 0:
            local_refine(netlist, iterations=int(cfg["refine_iters"]))

        new_anchors = compute_anchors(
            netlist,
            cfg["bin_w"],
            cfg["bin_h"],
            beta=cfg.get("beta", 0.6),
        )
        for (cid, tx, ty, w) in new_anchors:
            anchors[cid] = (cid, tx, ty, w)

        hp = net_hpwl(netlist, _pos(netlist))
        ov = total_overlap_area(netlist)
        history.append({"iter": it, "hpwl": hp, "overlap": ov})

    # ---- Stage 3a：合法化（消除重叠） ----
    legalize(netlist, cfg["legal_bin_w"], cfg["legal_bin_h"])
    history.append({
        "iter": max_iter,
        "hpwl": net_hpwl(netlist, _pos(netlist)),
        "overlap": total_overlap_area(netlist),
    })

    # ---- Stage 3b：详细布局（HPWL 局部优化） ----
    detailed_place(
        netlist,
        iterations=int(cfg["detail_iters"]),
        step=float(cfg["detail_step"]),
    )
    history.append({
        "iter": max_iter + 1,
        "hpwl": net_hpwl(netlist, _pos(netlist)),
        "overlap": total_overlap_area(netlist),
    })

    return history
