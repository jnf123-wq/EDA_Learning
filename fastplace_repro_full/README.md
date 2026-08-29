# FastPlace 完整流程复现（含详细布局）

在 `Fastplace_repro`（全局布局最小复现）的基础上，补齐 FastPlace 论文
          - Cell Shifting (paper version): shift boundaries + linear mapping + pseudo-pin beta
Local Refinement and a Hybrid Net Model》中的完整三阶段流程，并新增
**Stage 3：Legalization + Detailed Placement（合法化 + 详细布局）**。

## 完整流程

```
Stage 1  Global Optimization
          ├─ Hybrid Net Model：2~3 pin 用 clique，>=4 pin 用 star，权重 1/(p-1)
          ├─ 二次规划求解：min sum w_ij * (x_i - x_j)^2  ->  Q x = b
          └─ Cell Shifting：bin 密度 + 伪锚点扩散
Stage 2  Iterative Local Refinement
          └─ HPWL 8 邻域局部搜索（与 Stage 1 交错执行）
Stage 3  Legalization + Detailed Placement
          ├─ Legalization：网格贪心合法化，消除重叠
          └─ Detailed Placement：Cell Move + Cell Swap（HPWL 优化）
```

## 目录

```
Fastplace_repro_full/
├── config.yaml          # 参数（含 Stage 3 参数）
├── run.py               # 一键运行
├── data/toy.json        # 测试网表
├── src/
│   ├── netlist.py       # 网表数据结构 + JSON 解析
│   ├── netmodel.py      # 混合网表模型 -> 二次型矩阵
│   ├── qpsolver.py      # 解 Q x = b
│   ├── cell_shifting.py # bin 网格 + 密度搬移
│   ├── refinement.py    # HPWL 局部精化（Stage 2）
│   ├── legalization.py  # 合法化（Stage 3a，新增）
│   ├── detailed.py      # 详细布局（Stage 3b，新增）
│   ├── metrics.py       # HPWL / 重叠面积
│   ├── placer.py        # 三阶段主流程
│   └── viz.py           # 出图
└── tests/               # 单元测试（含合法化/详细布局测试）
```

## 运行

```bash
python run.py
python run.py --netlist data/toy.json --out layout.png
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## Stage 3 说明

- **Legalization**：把每个可动器件吸附到距离原位置最近的空闲 bin 槽，
  并标记其覆盖的 bin，从而保证零重叠、器件在板内。
- **Detailed Placement**：交替执行
  - Cell Move：单器件移动到相邻合法位置，接受 HPWL 下降；
  - Cell Swap：交换两个同尺寸器件，接受 HPWL 下降。

  Cell Swap 只交换同尺寸器件，因此天然保持合法（与标准单元布局中
  "交换同宽单元"一致；对功率 PCB 的矩形元件，只交换宽高相同的元件）。

## 与论文的对应

| 论文阶段 | 本仓库模块 |
|---|---|
| Global Optimization + Cell Shifting | `netmodel.py` / `qpsolver.py` / `cell_shifting.py` |
| Iterative Local Refinement | `refinement.py` |
| Detailed Placement | `legalization.py` + `detailed.py` |

> 注：论文针对标准单元按行做合法化，本复现针对矩形块（更接近功率 PCB 元件）
> 采用二维 bin 网格贪心合法化，属于教学级的简化等价实现。


## Cell shifting (paper version)
- Shift x-column / y-row boundaries so every interval width/height is proportional to the movable-cell area inside it.
- Linearly map every movable cell onto the shifted boundaries (order-preserving), giving a target position.
- Add the target as a pseudo pin with weight `beta` (see `config.yaml`) and re-solve the QP system.
- Kept `compute_utilization` for diagnostics; see `src/cell_shifting.py`.
