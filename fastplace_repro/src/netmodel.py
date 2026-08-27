from itertools import combinations

import numpy as np
from scipy import sparse

from netlist import Netlist


def build_system(netlist: Netlist, anchors=None):
    """把网表转成二次型系统。

    返回:
        Q     : 稀疏拉普拉斯矩阵 (N x N)
        dx, dy: 伪锚点产生的右端项 (N,)
        id_to_idx : cell id -> 变量下标
        dummy_idx : 大网 id -> star 虚拟节点下标
    """
    id_to_idx = {cid: i for i, cid in enumerate(netlist.cell_ids())}
    n_cells = len(id_to_idx)

    # >=4 pin 的网使用 star 模型，每个网加一个虚拟节点
    dummy_idx = {}
    dummy_count = 0
    for net in netlist.nets:
        if len(net.pins) > 3:
            dummy_idx[net.id] = n_cells + dummy_count
            dummy_count += 1

    N = n_cells + dummy_count
    rows, cols, vals = [], [], []
    dx = np.zeros(N)
    dy = np.zeros(N)

    def add_edge(i, j, w):
        rows.extend([i, j, i, j])
        cols.extend([i, j, j, i])
        vals.extend([w, w, -w, -w])

    for net in netlist.nets:
        p = len(net.pins)
        if p < 2:
            continue
        w = 1.0 / (p - 1)  # 归一化权重，使二次型尽量逼近 HPWL
        if p <= 3:
            # clique：所有 pin 两两相连
            for a, b in combinations(net.pins, 2):
                add_edge(id_to_idx[a], id_to_idx[b], w)
        else:
            # star：所有 pin 连到同一个虚拟节点
            d = dummy_idx[net.id]
            for a in net.pins:
                add_edge(id_to_idx[a], d, w)

    # cell shifting 产生的伪锚点：cell 与固定目标点之间的 2-pin 伪网
    if anchors:
        for (cell_id, tx, ty, w) in anchors:
            i = id_to_idx[cell_id]
            rows.append(i)
            cols.append(i)
            vals.append(w)
            dx[i] += w * tx
            dy[i] += w * ty

    Q = sparse.coo_matrix((vals, (rows, cols)), shape=(N, N)).tocsc()
    return Q, dx, dy, id_to_idx, dummy_idx
