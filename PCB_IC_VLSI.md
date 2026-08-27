# PCB、IC、VLSI 的区别及其 EDA 考量差异

**方向：功率 PCB 自动布局算法设计与优化（背景知识）**  
**整理时间：2026 年 8 月**

---

## 0. 三者概念与关系（先厘清）

- **PCB（Printed Circuit Board，印制电路板）**：承载并互连**分立元器件**的"基板/载体"，属于**板级（board-level）**设计。
- **IC（Integrated Circuit，集成电路）**：把电路集成在**一块芯片（die）**内，属于**芯片级（chip-level）**设计。IC 是一个**广义概念**，含模拟 IC、数字 IC、混合信号 IC、存储器等。
- **VLSI（Very-Large-Scale Integration，超大规模集成电路）**：IC 的**一个子类**，特指**规模极大（百万～十亿晶体管）的数字集成电路**（ASIC / SoC）。在 EDA 语境中，"VLSI EDA"通常等同于**数字 ASIC/SoC 的物理设计流程（RTL→GDSII）**。

> 关系：**VLSI ⊂ IC（数字、超大规模）**；**PCB 与 IC/VLSI 是两个层级**——PCB 上装的是 IC 封装和其他分立器件。

---

## 1. 三者的本质区别

| 维度 | **PCB** | **IC（模拟/定制为主）** | **VLSI（数字 ASIC/SoC）** |
|---|---|---|---|
| 设计对象 | 电路板（基板 + 焊盘 + 铜走线） | 芯片内晶体管/器件版图 | 芯片内标准单元/宏模块版图 |
| 基本单元 | **分立器件**（电阻、电容、电感、IC 封装、连接器），是"目录采购件" | 晶体管、电阻、电容等**器件级图形** | **标准单元（std cell）** + **宏模块（macro，如 SRAM/IP）** |
| 物理尺度 | 毫米级（走线微米～毫米，板厚毫米级） | 纳米～微米级 | **纳米级**（5nm/3nm/2nm…） |
| 器件/单元规模 | 几十～数千（高端可上万） | 几十～数千器件 | **百万～十亿**晶体管/单元 |
| 空间结构 | 2D 多层板，**双面**（Top/Bottom） | 2D 单面 | 2D 单面（标准单元按行） |
| 制造方式 | PCB 制造（蚀刻/压合/钻孔/电镀）+ 元器件**贴装焊接** | 晶圆代工（光刻、刻蚀、掺杂）+ 封装 | 晶圆代工（光刻等）+ 封装 |
| 最终输出 | **Gerber / ODB++** + 钻孔文件 + BOM + 装配文件 | **GDSII / OASIS** | **GDSII / OASIS** |

---

## 2. EDA 流程的区别

### 2.1 PCB 的 EDA 流程

```
原理图设计（schematic）→ 生成网表（netlist）
   → 封装/Footprint 库 → 器件布局（placement）
   → 布线（routing）→ DRC/DFM 检查
   → Gerber 输出 → 制板 + 元件贴装
```

- 入口是**原理图**（电气连接关系），器件来自**封装库**。
- 强调**可制造性（DFM）/可装配性（DFA）**、SI/PI、热、EMC。
- 常用工具：Cadence Allegro / OrCAD X、Altium Designer、Siemens Xpedition、Zuken CR-8000、KiCad；SI/PI 用 Sigrity / HyperLynx；热用 Icepak / FloTHERM。

### 2.2 VLSI（数字 ASIC/SoC）的 EDA 流程

```
RTL（HDL 描述）→ 逻辑综合（synthesis，生成门级网表）
   → 布图规划（floorplanning）→ 电源规划（power planning）
   → 布局（placement）→ 时钟树综合（CTS）
   → 布线（routing）→ 寄生提取（RC extraction）
   → 签核（signoff）：STA / DRC / LVS / IR-drop → tape-out（GDSII）
```

- 入口是 **RTL/HDL**，经**综合**转成**标准单元网表**。
- 强调**时序收敛（STA）**、拥塞、功耗、IR-drop。
- 常用工具：Synopsys（Fusion Compiler / ICC2 / DC / PrimeTime / StarRC）、Cadence（Innovus / Genus / Tempus / Quantus）、Siemens（Calibre）、Ansys（RedHawk / Totem）。

### 2.3 模拟 IC 的 EDA 流程（简）

```
原理图（schematic）→ SPICE 仿真 → 全定制版图（manual/custom layout）
   → DRC/LVS → RC 提取 → 后仿真（post-layout simulation）
```

- 器件级**手工/定制**版图为主，重视**匹配、寄生、对称性**。
- 常用工具：Cadence Virtuoso、SPICE（Spectre / HSPICE）、Calibre / IC Validator。

---

## 3. EDA 各环节的考量差异

| EDA 环节 | PCB | VLSI（数字） |
|---|---|---|
| **设计入口** | 原理图 + 封装库 | RTL + 标准单元库 |
| **库** | Footprint（封装外形/焊盘），器件为采购件 | Std cell（等高、含时序/功耗模型）、macro |
| **"单元"放置** | 异质器件、**双面 + 任意旋转** | 标准单元**按行（row）**摆放、朝向基本固定 |
| **布线** | 多层铜、宽电源/地平面、控阻抗、差分对、多种过孔 | 多层金属（5–20+）、极密集、曼哈顿走线、电源网格 |
| **首要目标** | 可布性、线长、**热 / EMI / PI / SI / DFM** | **时序（setup/hold）**、线长、拥塞、功耗、密度 |
| **约束类型** | 间距/clearance、keepout、固定件、安规、机械配合 | 时序、密度、时钟、电源/IR、工艺 DRC |
| **验证/签核** | DRC、DFM、SI/PI/EMI/热仿真、电气测试 | **STA**、DRC、LVS、寄生提取、IR-drop |
| **制造对接** | 制板厂 + 组装厂 | 晶圆代工厂（foundry） |

---

## 4. Placement 问题的差异（与本课题最相关）

这是把 VLSI 布局算法搬到 PCB 时必须理解的关键差异：

| 差异点 | PCB placement | VLSI placement |
|---|---|---|
| **规模** | 百～千（大板上万） | **百万～十亿单元** |
| **单元异质性** | **高度异质**（0402 电阻到大型 BGA/连接器，尺寸悬殊） | 标准单元**等高**（仅宽度不同），宏为少数大块 |
| **自由度** | **双面（Top/Bottom）** + **0/90/180/270 旋转** | **单面**，单元行内固定朝向（旋转受限） |
| **目标函数** | 线长 + 密度 + net crossing + **热/EMI/PI/机械** | 线长 + 密度 + **时序** + 拥塞 + 功耗 |
| **硬约束** | 间距、keepout、固定件、安规/绝缘、禁布面、机械高度 | 时序、密度、时钟、IR、工艺 DRC |
| **自动化程度** | 长期**半自动**（人在环），解析式刚起步（Cypress） | **全自动、成熟**（ePlace/RePlAce/DREAMPlace/ICC2/Innovus） |
| **可制造性** | DFM/DFA 强相关（组装、焊接、测试） | 工艺 DRC、CMP、光刻相关 |

> **一句话**：VLSI placement 是"**大规模、同质单元、单面、时序主导**"；PCB placement 是"**小规模、异质单元、双面可旋转、热/EMI/机械/功率主导**"。因此 **VLSI placer 不能直接搬到 PCB**，但**解析式方法论可迁移**（Cypress 即"VLSI-inspired"）。

---

## 5. 对"功率 PCB 自动布局"课题的启示

1. **方法论可借鉴、目标需重写**：VLSI 的解析式框架（密度势 + 平滑线长 + GPU）可迁移到 PCB，但目标必须替换为功率板的**回路面积、热、EMI、PI、间距/安规**等。

2. **自由度差异是难点也是创新点**：PCB 的**双面 + 旋转 + 异质外形**使 density/clearance 建模更复杂（Cypress 专门处理了旋转与双面的 density map），这是功率 PCB 布局里绕不开的工程点。

3. **约束的"软硬分离"更重要**：PCB 有大量**硬性物理约束**（安规间距、绝缘边界、固定件、禁布面），比 VLSI 更依赖"软引导 + 精确 legalizer"的组合。

4. **验证口径不同**：VLSI 用 STA/DRC/LVS/IR 签核；功率 PCB 用 **EMI/热/PI 仿真 + DFM** 签核——你的算法评估必须以后者为准，不能只比线长/时间。

---

### 主要参考来源
- 维基百科「放置与布线」；CSDN「版图设计与 PCB 设计的异同」；电子发烧友「IC 设计与 PCB 设计区别」
- EcrioniX「VLSI Physical Design Flow」；e-works「ASIC 设计流程」；CSMC-SNPS 参考流程
- Cypress（ISPD 2025）slides：PCB 双面/旋转的 density map 处理