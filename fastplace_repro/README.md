# FastPlace 最小复现

一个极简的 FastPlace 风格解析式布局器，用于理解
**二次线长求解 + 单元搬移（cell shifting）+ 迭代式局部精化 + 混合网表模型**。

## 目录
```
fastplace_repro/
├── config.yaml          # 参数
├── run.py               # 一键运行
├── data/toy.json        # 测试网表
├── src/
│   ├── netlist.py       # 网表数据结构 + JSON 解析
│   ├── netmodel.py      # 混合网表模型 -> 二次型矩阵
│   ├── qpsolver.py      # 解 Q x = b
│   ├── cell_shifting.py # bin 网格 + 密度搬移
│   ├── refinement.py    # HPWL 局部精化
│   ├── metrics.py       # HPWL / 重叠面积
│   ├── placer.py        # 主循环
│   └── viz.py           # 出图
└── tests/               # 单元测试
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

## 说明
- 这是**全局布局**，不保证零重叠；零重叠是后续 legalization 的工作。
- 2~3 pin 网用 clique 模型，>=4 pin 网用 star 模型（混合网表模型）。
- cell shifting 用 bin 利用率 + 伪锚点把器件推向稀疏 bin。
- local refinement 用 HPWL 在相邻位置做局部搜索。
