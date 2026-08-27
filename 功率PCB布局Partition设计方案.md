# 功率PCB自动布局：Partition（器件打包 / 分区）设计方案

> 面向框架：Cypress 类解析式布局（连续全局布局 + 密度 + 朝向 + 合法化）。
> 目标：先把“功率器件 + 紧密相关器件”打包为**功能单元（power cell）**，再按**电压域 / 隔离域**做二次打包与分区，形成多层级布局单元，供解析式布局器作为“粗粒度变量 + 约束”使用。
> 配套文档：《功率PCB硬约束目标函数形式化.md》。

---

## 0. 为什么把 Partition 作为前置任务

解析式布局直接对所有器件做连续优化，功率PCB会有三个问题：

1. **维度大但冗余**：去耦电容、栅极电阻、缓冲器必须贴着功率器件，独立优化既浪费自由度，又容易在中间迭代被密度/线长项“拉散”。
2. **硬约束难以用纯连续变量表达**：输入电容必须紧贴 IC、栅极驱动回路要短、初/次级要隔离。把它们固化成“包”后，约束变成包级/域级关系，更稳。
3. **功率电路是强 motif**：buck/boost/PFC/LLC 等拓扑有固定的“功率级子图”，适合先识别、再打包，而不是让聚类算法盲猜。

**结论**：把“功能 motif → 包 → 电压域组 → 隔离分区”做成**层级化的布局单元**，解析式算法先优化包间/域间布局，再在包内做精细布局。

---

## 1. 层级结构定义

| 层级 | 名称 | 组成 | 物理含义 |
|---|---|---|---|
| **L0** | 器件 primitive | 单个元件 + 引脚 + 电压域 + 功率等级 | 最小布局单元 |
| **L1** | 功能包 power cell / cluster | 1 个功率器件 + 与其强耦合的电容/电阻/缓冲器 | 一个功率级功能子图 |
| **L2** | 电压域组 voltage-domain group | 同一电压轨 / 同一隔离域的多个包 | 一块“电源岛” |
| **L3** | 隔离分区 isolation zone | 按初/次级、高低 dv/dt、热区划分的板级区域 | 宏观布局约束 |

分层的好处：解析式算法可以在 L2/L3 先做**包间布局**（粗），再在 L1 内做**包内精调**（细），类似 floorplanning → placement 的两阶段。

---

## 2. 核心数据模型（建议 JSON Schema）

```jsonc
{
  "board": { "width": 100.0, "height": 80.0, "layers": 4 },

  "components": [
    {
      "id": "Q1",
      "role": "power_mosfet",          // 功率器件角色标签，见 §3
      "voltage_domain": "VIN_48V",      // 电压域
      "net_class": "power",             // power | signal | sense | gate
      "power_w": 1.2,                   // 功耗 W（用于热目标）
      "package": { "body": [6.5, 5.0], "pins": [ {"name":"D","x":0.5,"y":2.5}, ... ] },
      "fixed": false,
      "orientation": ["N","E","S","W"]
    }
  ],

  "nets": [
    { "id":"SW", "pins":[{"comp":"Q1","pin":"D"},{"comp":"L1","pin":"1"}], "type":"switching" }
  ],

  "partitions": {
    "cells": [
      {
        "id":"CELL_HS_BUCK",
        "type":"buck_high_side",         // motif 模板类型
        "members":["Q1","Rg1","Cboot","Cbyp"],
        "anchor":"Q1",                    // 锚点器件（包内坐标相对它）
        "rigid":false,                    // rigid=平移刚体；false=软弹簧
        "voltage_domain":"VIN_48V"
      }
    ],
    "groups": [
      {
        "id":"GROUP_PRIMARY",
        "voltage_domain":"PRIMARY",
        "cells":["CELL_HS_BUCK","CELL_PFC"],
        "ground":"PGND",
        "keepout":["SECONDARY"]
      }
    ]
  }
}
```

---

## 3. 器件角色标注（role tagging）

打包前先给每个器件打标签，标签决定它属于哪种功能包。这是**规则驱动**的第一步，不靠算法猜。

| role 标签 | 典型器件 | 打包倾向 |
|---|---|---|
| `power_mosfet` / `power_diode` / `sync_rect` | MOSFET、二极管、SR | 作为包的**锚点** |
| `gate_driver` | 栅极驱动 IC | 与所驱动的 MOSFET 打包 |
| `controller` | 控制 IC | 与反馈/补偿网络打包，但远离 SW/磁性件 |
| `inductor` / `transformer` | 电感、变压器 | 作为“发热+漏磁”器件，单独/就近打包 |
| `cap_input` / `cap_output` / `cap_bulk` | 输入/输出/大电容 | 紧贴对应功率器件 |
| `cap_decoup` / `cap_boot` / `cap_snubber` | 去耦/自举/缓冲电容 | 分别贴 IC、SW、SW |
| `res_gate` / `res_gs` | 栅极电阻、栅源电阻 | 贴 driver 或 MOSFET 栅极 |
| `res_sense` / `divider` | 采样电阻、分压电阻 | 贴控制器 sense/FB 引脚，远离 SW |
| `connector` / `fuse` / `tvs` | 端口、保险丝、TVS | 板级定位，通常 fixed/anchored |
| `heatsink` / `mech` | 散热器、机械件 | fixed，参与热/禁布约束 |

---

## 4. L1 打包规则：功率器件 + 紧密器件

### 4.1 方法 A：自底向上凝聚聚类（无模板时）

把网表建成**超图**：节点 = 器件，超边 = 网络；再叠加功率专用边：

- 功率回路边（hot loop）：`MOSFET ↔ 输入/输出电容 ↔ 地`，权重高；
- 栅极驱动边：`driver ↔ MOSFET gate/source`，权重高；
- 采样/反馈边：`controller ↔ 采样电阻/分压电阻`，权重中；
- 热耦合边：两器件都高功耗且空间近，权重低（用于热分散，通常反而不该打包）。

**聚类代价函数**（判断两个簇是否合并）：

```
merge_cost(C_i, C_j) = -α·affinity(C_i,C_j)
                       + β·voltage_penalty(C_i,C_j)   // 不同电压域尽量不要混包
                       + γ·area(C_i ∪ C_j)            // 包面积膨胀惩罚
                       + δ·thermal_penalty(C_i,C_j)   // 高功耗器件聚集惩罚
```

其中 `affinity` 可用超图切割增益（cut size）或谱聚类相似度近似。每次合并取代价最小的对，直到满足阈值或达到 motif 规模上限。

### 4.2 方法 B：基于 motif 模板的种子聚类（**推荐，功率PCB更稳**）

1. **选种子**：每个 `power_mosfet / power_diode / sync_rect / gate_driver / controller` 都作为一个包种子。
2. **按模板吸附**：依据网表连接与角色，把强耦合器件并入种子包。例如 buck 高边 MOSFET 的包要吸入 `Cboot`、`Rg`、`Cbyp`、就近的 `Cin`/`COUT` 的一个子集。
3. **冲突消解**：一个电容同时被多个包候选时，按 `边权 = 电流大小 × 1/寄生敏感度` 择优归属。
4. **固定器件的处理**：连接器、散热器、机械件不并入包，作为 L3 区域约束。

### 4.3 打包判定指标（一个包是否成立）

- 包内网络数 / 包间网络数之比高（内部耦合强）；
- 包内器件到锚点的 pad-to-pad 距离敏感度高（电流大、dv/dt 高）；
- 包的总面积 < 预设上限（例如占板面积 5%），避免“包太大失去精细布局意义”；
- 包不跨越隔离域（初/次级不能同包）。

---

## 5. L2 电压域打包（同电压域二次打包）

把 L1 的功能包按**电压域**聚成组：

```
GROUP = { cells | same voltage_domain AND same isolation_domain AND same ground_class }
```

关键规则：

| 规则 | 说明 |
|---|---|
| 同电压轨 | 同一 `voltage_domain`（如 `+12V_POWER`）的包聚为一组 |
| 隔离域分离 | PRIMARY / SECONDARY 分属不同组，且组间设置 keepout / creepage |
| 地分组 | `PGND`（功率地）与 `AGND`（模拟地）分属不同簇，只在单点（thermal pad）汇合 |
| 高低 dv/dt | SW 类节点所在组与 `sense/FB` 组之间保持最小间距 |

**输出的电压域组**可作为解析式布局里的**区域/岛屿约束**：同一组的质心被约束在一个连通区域；不同隔离组之间加排斥/间距势。

---

## 6. L3 隔离分区（板级宏观布局）

| 分区 | 内容 | 目标 |
|---|---|---|
| 功率级区 | MOSFET/二极管/电感/变压器/大电容 | 回路面积小、铜皮宽 |
| 控制/模拟区 | 控制器、补偿、采样 | 远离 SW 与磁性件 |
| 输入/输出端口区 | 连接器、保险丝、TVS | 固定，靠近板边 |
| 初/次级隔离带 | 隔离变压器的两侧 | 满足爬电/电气间隙 |
| 散热区 | 散热器、高功耗器件、热过孔 | 热源分散，靠近散热边界/铜区 |

这些分区不直接“打包”，而是转成 L3 级约束：**区域边界、禁布区、最小间距、相对方位**。

---

## 7. 把 Partition 接入解析式布局

### 7.1 两种包模型

1. **刚性包（rigid）**：包内器件相对锚点固定，布局器只优化包的平移（+朝向）。适合输入/输出电容、自举电容这类“必须贴着”的元件。变量：包质心 `(X_g, Y_g, θ_g)`。
2. **软包（soft cluster）**：包内器件用二次弹簧连到包质心，允许少量相对位移。适合需在密度/线长间折中的包。

### 7.2 目标函数扩展

在原解析式目标 `L = λ_WL·WL + λ_D·D` 上增加：

```
L = λ_WL·WL + λ_D·D
    + λ_cluster · Σ_g Σ_{i∈g} w_i · ‖x_i − (X_g + R(θ_g)·r_i)‖²     // 包内聚合力
    + λ_group  · Σ_G Σ_{g∈G} w_g · ‖X_g − C_G‖²                      // 电压域组内聚合力
    + λ_iso    · Σ_{G≠G'} H(d_min − ‖C_G − C_G'‖)                    // 隔离域间距
```

`r_i` 是器件在包内相对锚点的参考偏移，`R(θ)` 是旋转矩阵。

### 7.3 分层求解流程

1. 在 L2/L3 层优化“组质心”，做电压域分区；
2. 固定组质心，在组内优化 L1 包的质心与朝向；
3. 固定包质心，在包内优化 L0 器件；
4. 最后做合法化（legalization），恢复 DRC/间距。

这正好呼应 Cypress“连续全局布局 → 朝向 → 合法化”的思路，只是把变量组织成层级。

---

## 8. 典型拓扑的包模板（可直接当规则库）

### 8.1 同步 Buck（分立功率级）
```
CELL_HS = {Q_HS, Rg_HS, Cboot}
CELL_LS = {Q_LS, Rg_LS, Cbs_byp}
CELL_OUT = {L, C_out(近端), C_out(bulk)}
GROUP_BUCK = CELL_HS ∪ CELL_LS ∪ CELL_OUT ∪ {controller, C_in, sense/divider}
```
- `C_in` 贴 HS MOSFET/IC 的 PVIN 与 PGND。
- `L` 与 SW 节点铜皮面积最小。

### 8.2 集成开关 Buck（单 IC）
```
CELL = {IC, C_in, C_boot, L, C_out(近端), divider, comp}
```
- `C_in` 第一优先，`L/SW` 第二，`C_out` 第三。

### 8.3 Boost
```
CELL = {L, SW 开关管, 整流二极管/SR, C_in, C_out}
```
- 输出电容贴 IC/二极管（脉冲电流回路最短）。

### 8.4 PFC（Boost 型）
```
CELL_PFC = {MOSFET, diode, L_boost, C_out, current_sense}
```

### 8.5 LLC
```
CELL_PRI = {Q1,Q2, Cr, Lr, 变压器初级}
CELL_SEC = {SR1,SR2, C_out}
GROUP_PRI / GROUP_SEC 分属隔离域，组间 keepout。
```

### 8.6 栅极驱动（Infineon 2EDN/1EDN 指南）
```
CELL_GATE = {gate_driver, C_byp(VDD), Rg, Rgs, (ferrite bead)}
```
- `C_byp` 贴 driver，且 ≤ 包尾部；
- driver 贴 MOSFET，缩短 gate/source 走线；
- VDD 与 GND 走线成对贴近，抵消磁场。

---

## 9. 评价与验收指标

| 指标 | 定义 | 目标 |
|---|---|---|
| 包间网络割 | 跨包网络的 HPWL/数量 | 越小越好 |
| 包内耦合度 | 包内网络数 / 总网络数 | 越高越好 |
| 电压域纯度 | 包内是否跨隔离域 | 必须为 0 |
| 回路面积 | 各 hot loop 的 pad 级面积/长度 | 越小越好 |
| 隔离间距 | 不同电压级组间最小距离 | ≥ 规则要求 |
| 热分散度 | 高功耗器件的最近邻距离 | 越大越好（避免聚集） |

---

## 10. 伪代码

```text
function build_partition(netlist, constraints):
    roles = tag_roles(netlist, constraints)          # §3
    cells = []
    for power_dev in roles.power_devices:
        cell = new_cell(anchor=power_dev)
        for nb in neighbors(power_dev):
            if role(nb) in attach_rule(power_dev) and same_domain(nb, power_dev):
                cell.add(nb)                          # 依模板吸附
        cells.append(cell)
    resolve_conflicts(cells)                          # 一个器件只属一个包

    groups = group_by_voltage_domain(cells)           # L2
    zones  = build_isolation_zones(groups, constraints)  # L3

    return {cells, groups, zones}
```

---

## 11. 待确认/下一步

- 选定最小网表格式（建议 JSON + 一个真实小功率板，如 TI LM5177 或 Infineon 800W 案例的一小块）。
- 决定包是 **rigid** 还是 **soft**，先在一两个包上验证。
- 与《功率PCB硬约束目标函数形式化.md》中的 `E_loop / E_iso / E_thermal` 对接，把这些目标作用在“包”的质心与 pad 坐标上。
