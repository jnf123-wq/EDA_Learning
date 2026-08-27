import numpy as np
from scipy.sparse import eye
from scipy.sparse.linalg import spsolve


def solve(Q, dx, dy, fixed_mask, fixed_xy):
    """解 Q x = dx、Q y = dy，固定节点保持 fixed_xy 不变。"""
    Q = Q.tocsc()
    N = Q.shape[0]
    movable = ~fixed_mask

    Qmm = Q[movable][:, movable].tocsc()
    Qmf = Q[movable][:, fixed_mask].tocsc()

    bm_x = dx[movable] - Qmf @ fixed_xy[fixed_mask, 0]
    bm_y = dy[movable] - Qmf @ fixed_xy[fixed_mask, 1]

    # 小正则项：无固定点时防止矩阵奇异；有固定点时数值更稳
    diag = np.abs(Qmm.diagonal())
    eps = 1e-12 * (float(diag.mean()) + 1.0) if diag.size else 1e-12
    Qreg = (Qmm + eps * eye(Qmm.shape[0], format="csc")).tocsc()

    xm = spsolve(Qreg, bm_x)
    ym = spsolve(Qreg, bm_y)

    pos = np.zeros((N, 2))
    pos[fixed_mask] = fixed_xy[fixed_mask]
    pos[movable, 0] = xm
    pos[movable, 1] = ym
    return pos

