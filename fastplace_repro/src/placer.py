import numpy as np

from netmodel import build_system
from qpsolver import solve
from cell_shifting import compute_anchors
from refinement import local_refine
from metrics import net_hpwl, total_overlap_area


def _pos(netlist):
    return {c.id: (c.x, c.y) for c in netlist.cells.values()}


def place(netlist, cfg):
    history = []
    anchors = {}

    for it in range(int(cfg["max_iter"])):
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

        # 单元搬移：持续记录/更新伪锚点，避免器件被线长项重新拉回原点
        new_anchors = compute_anchors(
            netlist,
            cfg["bin_w"],
            cfg["bin_h"],
            target_util=cfg["target_util"],
            spread_weight=cfg["spread_weight"],
        )
        for (cid, tx, ty, w) in new_anchors:
            anchors[cid] = (cid, tx, ty, w)

        hp = net_hpwl(netlist, _pos(netlist))
        ov = total_overlap_area(netlist)
        history.append({"iter": it, "hpwl": hp, "overlap": ov})

    return history
