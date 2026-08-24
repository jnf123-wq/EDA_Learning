如果你的参研课题是**“功率 PCB 自动布局算法设计与优化”**，我建议不要一上来只搜“PCB Placement”。更有效的路线是把知识分成三层：

1. **PCB 本体知识**：partition → floorplan → placement → routing → DRC/电气约束；
2. **EDA/Physical Design 算法知识**：把 PCB 问题和 VLSI 的 partition、floorplanning、placement、routing 联系起来；
3. **AI/优化方法**：Simulated Annealing、ILP/MILP、连续优化、RL、GNN、LLM/Agent 等。

尤其需要注意：**PCB placement 和 IC placement 名字相同，但问题结构并不完全一样**。PCB 元件有真实尺寸、旋转、双面、连接器/散热器/机械约束、功率回路、EMI/EMC、热约束等；而 IC placement 更多围绕标准单元、宏单元、die area、density、timing、congestion 等展开。不过二者的算法思想高度相通，所以你的课题非常值得系统学习 VLSI physical design。

下面我按“一个大四 EDA 实习生应该怎样入门”的方式整理。

---

# 一、先建立整体认识：PCB Physical Design 到底在做什么？

可以先把一个 PCB 自动布局系统抽象成：

```text
Schematic / Netlist
       │
       ▼
  Functional Partition
       │
       ▼
     Floorplan
       │
       ▼
    Placement
       │
       ▼
  Global Routing
       │
       ▼
 Detailed Routing
       │
       ▼
 DRC / SI / PI / Thermal / EMC
       │
       ▼
     QoR
```

其中：

- **Partition**：决定“哪些元件属于一个功能模块”
- **Floorplan**：决定“这些模块应该放在哪里”
- **Placement**：决定“每个具体元件的精确位置和朝向”
- **Routing**：决定“不同元件之间的铜线怎么走”
- **Optimization**：不断在上述步骤之间迭代

PCB 物理布局的数学本质可以理解为：

> 在满足大量几何、电气、制造、热、EMI/EMC 约束的条件下，对元件位置和互连路径进行多目标组合优化。

PCB placement/routing 本身就是一个非常典型的组合优化问题。比较经典的 PCB 物理布局综述是 Abboud、Grötschel、Koch 的 **“Mathematical methods for physical layout of printed circuit boards: An overview”**，专门讨论 PCB component placement 和 wire routing 的数学模型与算法。

---

# 二、Partition：为什么 PCB 也需要“划分”？

## 2.1 什么是 Partition？

Partition 的核心思想是：

> **不要直接把整个 PCB 当成一个巨大问题，而是先把它拆成若干有意义的子问题。**

例如一个典型功率板：

```text
                ┌───────────────┐
                │ Control Logic │
                │ MCU / DSP     │
                └───────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
 ┌────────────┐  ┌─────────────┐  ┌─────────────┐
 │ Power      │  │ Gate Driver │  │ Feedback    │
 │ Stage      │  │             │  │ / Sensing   │
 └────────────┘  └─────────────┘  └─────────────┘
        │
        ▼
 ┌────────────┐
 │ DC / AC     │
 │ Interface   │
 └────────────┘
```

比如一个 Buck Converter，可以自然形成：

- 输入电容模块
- MOSFET/功率开关模块
- Gate Driver
- Inductor
- Output Capacitor
- Feedback/Sense
- MCU/控制模块

Partition 后，优化器不必同时考虑所有元件，而可以先考虑：

> “Power Stage 应该位于哪里？”

然后再进一步：

> “Power Stage 内 MOSFET、Driver、Cin、Inductor 怎么放？”

---

## 2.2 Partition 的数学思想

在 EDA 中经常把电路表示成：

- Graph \(G=(V,E)\)
- \(V\)：元件/模块
- \(E\)：net/connection

然后进行：

\[
V=V_1\cup V_2\cup\cdots\cup V_k
\]

希望：

- 每个 partition 内部连接尽可能多；
- partition 之间的连接尽可能少；
- 每个 partition 的面积/资源比较平衡。

例如：

\[
\min Cut(V_1,V_2)
\]

同时：

\[
Area(V_1)\approx Area(V_2)
\]

这就会自然进入经典的：

- graph partitioning
- min-cut
- KL algorithm
- FM algorithm
- hypergraph partitioning

所以你以后看到 **FM / KL / hypergraph partitioning**，一定要联想到这里。

---

# 三、Floorplan：Partition 后决定“模块住哪里”

Partition 解决：

> **Who belongs together?**

Floorplan 解决：

> **Where should each group go?**

例如：

```text
┌──────────────────────────────────────┐
│                                      │
│             MCU / DSP                │
│                                      │
│                         Feedback     │
│                                      │
│     Gate Driver                      │
│                                      │
│   MOSFET → Inductor → Output         │
│                                      │
│ Input                                 │
└──────────────────────────────────────┘
```

这时候还没有必要决定：

> MOSFET 精确坐标是 (35.2, 21.7) mm。

只需要决定：

> Power Stage 在左下角，Control 在右上角。

这就是 **floorplanning**。

---

## 3.1 Floorplan 和 Placement 的区别

这是你实习中非常容易被问到的问题。

### Floorplan

粗粒度：

```text
[ MCU ] [ Communication ]

[ Driver ] [ Power Stage ]

[ Input ] [ Output ]
```

### Placement

细粒度：

```text
              MCU
        ┌──────────┐
        │          │
        └──────────┘

  C1   C2
   │    │
   ▼    ▼
 ┌───┐ ┌────┐
 │Cin│ │MOS │
 └───┘ └────┘
          │
          ▼
       ┌──────┐
       │ Lout │
       └──────┘
```

在 VLSI 领域，floorplanning 位于 placement 之前；placement 决定更细粒度的物理位置，routing 再根据 placement 决定实际互连。IEEE 对 placement 的介绍也明确把 floorplanning、placement、routing 看成连续的 physical-design stages。

---

# 四、Placement：这很可能是你课题的核心

你的课题叫：

> **功率 PCB 自动布局算法设计与优化**

所以最重要的就是理解 placement 到底在优化什么。

---

## 4.1 Placement 的输入

通常包括：

```text
Board Boundary
Component List
Footprints
Component Size
Rotation Constraints
Netlist
Pin Locations
Keep-out Regions
Layer Constraints
Design Rules
Electrical Constraints
Thermal Constraints
```

输出：

```text
Component i:
(x_i, y_i, rotation_i, layer_i)
```

因此一个 component 可以表示：

\[
C_i=(x_i,y_i,\theta_i,l_i)
\]

其中：

- \(x_i,y_i\)：坐标
- \(\theta_i\)：旋转角度
- \(l_i\)：层

---

# 五、Placement 到底优化什么？

这是以后读论文最重要的部分。

最简单的目标：

\[
\min Wirelength
\]

但真实 PCB 一般远远不止这个。

可以写成：

\[
\min
\alpha W
+\beta C
+\gamma V
+\delta T
+\epsilon E
+\zeta H
\]

其中：

- \(W\)：wirelength
- \(C\)：routing congestion
- \(V\)：via count
- \(T\)：thermal cost
- \(E\)：EMI/EMC 或 electrical penalty
- \(H\)：hard constraint violation penalty

---

## 5.1 Wirelength

最经典的是 HPWL：

\[
HPWL(net)=
(x_{max}-x_{min})
+
(y_{max}-y_{min})
\]

例如一个 net 连接：

```text
A ●────────────● B
        │
        ● C
```

HPWL 就是包住所有 pin 的最小矩形周长的一半。

这在 VLSI placement 里面极其重要。

---

## 5.2 Congestion

即使两个 placement：

```text
Placement A:
wirelength = 100
congestion = 20

Placement B:
wirelength = 90
congestion = 100
```

B 的 wirelength 更短，但可能根本 route 不出来。

所以现代 placement 越来越强调：

> **routability-driven placement**

即：

> placement 不能只考虑“线短不短”，必须考虑“后面能不能布得出来”。

这也是 PCB placement 非常重要的思想。

---

# 六、功率 PCB 为什么比普通 PCB 更有意思？

这点和你的课题高度相关。

普通 PCB 可以比较关注：

- wirelength
- routing
- DRC
- component density

但**功率 PCB**需要特别考虑：

### 1. 高 di/dt 回路

例如：

```text
MOSFET
   │
   │
  Cdec
   │
   └────── Power Loop
```

高频开关回路面积过大，会导致：

- EMI 增强
- parasitic inductance 增加
- voltage overshoot
- ringing

因此：

> **“两个元件之间的距离”并不是简单的几何问题，而是电气问题。**

---

### 2. Thermal

功率器件：

- MOSFET
- IGBT
- diode
- inductor
- transformer

都有明显的热问题。

因此 placement 目标可能包含：

\[
\min T_{max}
\]

或者：

\[
\min \sum_i P_i R_{\theta i}
\]

---

### 3. Power loop

功率 PCB 中一个非常重要的 placement concept 是：

> **Critical Current Loop**

例如 Buck：

```text
       VIN
        │
       Cin
        │
        ├──── MOSFET
        │       │
        │       ▼
        │      L
        │       │
        └───────┴── VOUT
```

布局算法可能需要直接把：

> Cin、High-side MOS、Low-side MOS、Gate Driver

作为一个强耦合 cluster。

所以你未来研究可以从：

> **netlist-based placement**

进一步发展到：

> **electrical-function-aware placement**

这很可能比单纯优化 HPWL 更适合功率 PCB。

---

# 七、Routing：Placement 后面真正“走线”

Routing 的问题可以简单理解为：

> 已经决定元件在哪里，现在把所有 net 连起来。

例如：

```text
A ●
   \
    \
     ──────● B

C ●────────● D
```

但实际 PCB routing 必须满足：

- trace width
- clearance
- via constraints
- layer constraints
- obstacle avoidance
- differential pair
- impedance
- length matching
- power/ground
- DRC

---

# 八、Global Routing vs Detailed Routing

这个概念建议你现在就掌握。

## Global Routing

不决定每一根铜线的精确几何形状，而决定：

> “这条 net 大概经过哪些区域/哪些 routing channels？”

例如：

```text
┌────┬────┬────┬────┐
│    │ →  │ →  │    │
├────┼────┼────┼────┤
│    │    │ →  │    │
├────┼────┼────┼────┤
│    │    │    │    │
└────┴────┴────┴────┘
```

---

## Detailed Routing

真正确定：

```text
(x1,y1)
   │
   ├───────────┐
   │           │
   └───────┐   │
           │   │
           ▼   ▼
          PAD  PAD
```

也就是：

- exact trace geometry
- exact via
- exact layer
- exact clearance

---

经典 VLSI routing literature 对 global routing 的定义和作用非常值得参考；Hu 和 Sapatnekar 的 survey 系统总结了 multi-net global routing，包括 sequential routing、rip-up-and-reroute、multicommodity flow 等方法。

---

# 九、你应该特别关注的几个算法范式

对于你的课题，我建议把论文按下面这条路线读。

| 方法 | 核心思想 | 对 PCB 的价值 |
|---|---|---|
| Partitioning | divide-and-conquer | 大规模 PCB |
| Simulated Annealing | 随机搜索 | placement 很经典 |
| Genetic Algorithm | evolutionary search | 多目标优化 |
| ILP/MILP | 数学精确优化 | 小/中规模 placement |
| Force-directed | 力模型 | 快速 global placement |
| Quadratic placement | 连续优化 | 理解 VLSI |
| Nonlinear optimization | 非线性优化 | 高质量 placement |
| A* | path search | routing |
| Rip-up & reroute | 失败后重新布线 | router |
| RL | sequential decision | 新一代 PCB PnR |
| GNN | graph representation | netlist/constraint learning |
| LLM/Agent | semantic + tool use | 新兴方向 |

---

# 十、强烈推荐你先看这几篇 PCB 文献

## 1. PCB Physical Layout 数学方法综述——入门第一篇

**N. Abboud, M. Grötschel, T. Koch, “Mathematical methods for physical layout of printed circuit boards: An overview”**

这是我最建议你**第一篇认真读**的 PCB algorithm paper。

它直接讨论：

- PCB placement
- PCB routing
- mathematical modeling
- optimization methods

而且比较适合作为从“电气工程学生”进入“EDA 算法”的桥梁。

[论文信息/可阅读版本](https://www.researchgate.net/publication/226021976_Mathematical_methods_for_physical_layout_of_printed_circuit_boards_An_overview?utm_source=chatgpt.com)

---

# 十一、第二篇：NS-Place——非常值得你研究

**“Net Separation-Oriented Printed Circuit Board Placement via Margin Maximization”**

这个非常贴近你的课题。

核心思想不是简单地：

\[
\min HPWL
\]

而是：

> 让不同 net 之间形成更好的空间 separation，从而改善后续 routability。

论文使用：

- maximum-margin formulation
- coordinate descent
- MILP legalization

并在 14 个 PCB design 上进行了实验。论文报告了 routed wirelength、via count 和 design-rule violations 的改善。

[NS-Place 论文](https://arxiv.org/abs/2210.14259?utm_source=chatgpt.com)

**这篇非常值得你重点看。**

因为它告诉你一个很重要的研究思想：

> Placement 的 objective 不一定直接优化最终 routing，而可以设计一个 proxy objective，让 placement 天然更容易 routing。

---

# 十二、第三篇：2026 年最新的 PCB Placement——建议重点关注

**“An analytical approach and fine-tuning strategy for PCB placement optimization”**

2026 年发表，核心流程：

```text
Global Placement
       ↓
Legalization
       ↓
Fine-tuning
```

使用 analytical placement，并结合：

- rigid-body rotation
- Hanan-grid-based legalization
- routability-oriented fine-tuning

并用开源 router 做最终验证。

[论文页面](https://www.sciencedirect.com/science/article/abs/pii/S016792602500224X?utm_source=chatgpt.com)

对于你来说，这篇特别有价值，因为它已经很接近：

> **“怎么设计一个现代 PCB placer”**

---

# 十三、第四篇：MARS-Place——2026 最新 PCB Placement

**“MARS-Place: Multi-stage alignment-refined strategy for PCB placement and routing optimization”**

2026 年的工作，把 PCB placement 分成：

```text
Initial Placement
       ↓
Detailed Placement
       ↓
Fine-tuning
```

其中引入：

- attractive force
- repulsive force
- alignment force
- adaptive exploration
- simulated annealing

并且把 placement 和 routing quality 联系起来。

[MARS-Place 论文页面](https://www.sciencedirect.com/science/article/pii/S016792602600026X?utm_source=chatgpt.com)

如果你现在开始做这个方向，我会把它列为**重点跟踪论文**。

---

# 十四、第五篇：PCBWorld——如果你想研究 AI/RL

**PCBWorld: A Benchmark Environment for Engine-Grounded PCB Design Automation**

这是 2026 年非常值得关注的新方向。

它把 PCB routing 与 **KiCad EDA engine**结合起来，让 agent/RL 系统不是在一个纯模拟环境中玩，而是直接通过 PCB engine 进行操作，并利用 DRC feedback。

它还提供了：

- synthetic PCB instances
- 679 个真实开源 PCB
- KiCad native `.kicad_pcb`
- DRC-based evaluation

等。

[PCBWorld 论文](https://arxiv.org/abs/2607.05915?utm_source=chatgpt.com)

如果你的导师以后想让你做：

> RL PCB Placement / Routing

这篇非常值得研究。

---

# 十五、再往前一步：OmniLayout / OmniRouting

这是 2026 年更前沿的一条路线。

### OmniLayout

研究：

> LLM / multimodal model 是否能够理解 PCB placement 的空间、电气和 routing constraints？

它使用了 **1,681 个工业级 PCB layout**，并设计了 placement reasoning、routability-aware placement、electrical functionality 等任务。

[OmniLayout](https://arxiv.org/abs/2607.03261?utm_source=chatgpt.com)

### OmniRouting

进一步研究：

> LLM 能不能理解 PCB routing？

同样有 1,681 个工业级 PCB，并考察：

- geometric routing
- DRC-aware routing
- electrical functionality
- tool-augmented agent

等。

[OmniRouting](https://arxiv.org/abs/2608.04434?utm_source=chatgpt.com)

不过对于你现在的阶段，**不要先学 LLM**。

先把传统 placement/routing 搞懂。

---

# 十六、非常推荐你直接研究 OpenROAD PCB 项目

这个对实习生尤其有价值，因为它不只是论文，而是：

> **论文 + benchmark + source code + router + placer**

Chung-Kuan Cheng 的研究主页列出了：

- PCB-PR-App
- KiCadParser
- SA-PCB
- PCB analytical placement
- PcbRouter

等项目。

[OpenROAD PCB 项目主页](https://cseweb.ucsd.edu/~kuan/?utm_source=chatgpt.com)

其中 **SA-PCB** 是一个基于 simulated annealing 的 PCB placement tool。

[SA-PCB GitHub](https://github.com/The-OpenROAD-Project-Attic/SA-PCB?utm_source=chatgpt.com)

如果我是你，我会：

> **论文看懂一篇 → 下载代码 → 跑起来 → 改 objective → 看结果**

而不是连续看 30 篇论文。

---

# 十七、然后进入 VLSI Physical Design 文献

这里非常重要。

虽然你的对象是 PCB，但是：

> **PCB Placement 的很多算法思想来自 VLSI Physical Design。**

你应该把下面这张知识地图记住：

```text
                 Physical Design
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Partitioning   Floorplanning   Placement
                                       │
                                       ▼
                                    Routing
```

---

# 十八、TCAD 是什么？

## TCAD = IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems

它不是 conference，而是：

> **IEEE 的 EDA 顶级期刊之一。**

官方 scope 覆盖：

- planning
- synthesis
- partitioning
- modeling
- simulation
- layout
- verification
- testing
- physical design
- power
- performance
- reliability
- security

等。

[IEEE TCAD 官方主页](https://ieee-ceda.org/publications/tcad?utm_source=chatgpt.com)

你可以简单记：

> **TCAD = EDA 领域的重要期刊**

如果你看到：

> IEEE TCAD

通常意味着这篇论文比较深入、完整，适合学习算法设计和实验方法。

---

# 十九、DAC 是什么？

## DAC = Design Automation Conference

这是 EDA 领域最重要的 conference 之一。

官方称 DAC 是 electronic circuits and systems design and automation 的 premier conference。

[DAC 官方主页](https://dac.com/?utm_source=chatgpt.com)

可以理解：

> **DAC = EDA 顶会中的“大平台”**

研究方向非常广：

```text
AI for EDA
Logic Synthesis
Physical Design
Verification
Architecture
Hardware Security
ML
Analog
System Design
```

如果以后你的 PCB placement 算法能够抽象成一般的 physical design / package / PCB optimization 问题，DAC 就是值得关注的 venue。

---

# 二十、ICCAD 是什么？

## ICCAD = IEEE/ACM International Conference on Computer-Aided Design

它是非常核心的 EDA conference。

官方称 ICCAD 是 EDA research 的 premier forum，并覆盖从 device/circuit 到 system level 的 CAD 问题。

[ICCAD 官方主页](https://iccad.com/?utm_source=chatgpt.com)

更重要的是：

**ICCAD 2026 的 CFP 明确列出了：**

- Floorplanning
- Placement
- Routing
- Physical Design
- Timing
- Power
- Signal Integrity
- Manufacturability

等方向。

所以如果你看到：

> ICCAD + placement/routing

基本就是和你的算法方向高度相关。

---

# 二十一、DATE 是什么？

## DATE = Design, Automation and Test in Europe

欧洲非常重要的 EDA conference。

它覆盖：

- design
- automation
- test
- manufacturing
- IC/SoC
- embedded systems
- hardware/software

等。

[DATE 官方主页](https://www.date-conference.com/?utm_source=chatgpt.com)

你可以简单记：

> **DATE = 欧洲 EDA 旗舰会议之一**

它的 scope 比纯 physical design 更广。

---

# 二十二、ASP-DAC 是什么？

## ASP-DAC = Asia and South Pacific Design Automation Conference

这个对你尤其重要，因为亚洲的 EDA 学术圈非常活跃。

官方称 ASP-DAC 是亚洲及南太平洋地区重要的 EDA/VLSI conference，自 1995 年开始举办。

[ASP-DAC 官方主页](https://www.aspdac.com/aspdac/?utm_source=chatgpt.com)

而且对你的课题有一个特别重要的信息：

**ASP-DAC 2026 CFP 直接把下面这些放进 Physical Design：**

> Floorplanning, partitioning, placement, routing optimization

并且明确包括：

> Package/PCB/3D-IC placement and routing 


所以：

### 你的 PCB placement 课题和 ASP-DAC 是直接匹配的。

这一点非常值得记下来。

---

# 二十三、ICML 是什么？

## ICML = International Conference on Machine Learning

这是机器学习领域的顶级会议之一。

它不是 EDA conference。

官方将 ICML 定义为 machine learning 领域的重要国际会议，涵盖 ML、AI、statistics、data science，以及 robotics、vision 等应用。

[ICML 官方主页](https://icml.cc/?utm_source=chatgpt.com)

对你的意义是：

假设你以后做：

```text
PCB Placement
      ↓
Reinforcement Learning
      ↓
Graph Neural Network
      ↓
Combinatorial Optimization
```

那么：

> **EDA 部分 → DAC / ICCAD / ASP-DAC / TCAD**

而：

> **ML algorithm 部分 → ICML / NeurIPS / AAAI**

---

# 二十四、NIPS 是什么？

你看到的 **NIPS** 是以前的名称。

现在叫：

> **NeurIPS = Conference on Neural Information Processing Systems**

NeurIPS 官方现在使用 NeurIPS 这一名称。2026 年是第 40 届。

[NeurIPS 官方主页](https://neurips.cc/?utm_source=chatgpt.com)

它是：

> **AI / Machine Learning 顶级会议**

重点方向包括：

- Deep Learning
- Reinforcement Learning
- Optimization
- Generative AI
- Computer Vision
- NLP
- Decision Making

等。

所以：

> **NIPS ≈ NeurIPS**

以后看论文不要把 NIPS 和另一个会议理解成两个东西。

---

# 二十五、AAAI 是什么？

## AAAI = Association for the Advancement of Artificial Intelligence

AAAI Conference 是人工智能领域非常重要的国际会议。

官方对 AAAI conference 的定位是促进 AI 研究和学术交流，覆盖 AI 的广泛方向。

[AAAI 官方主页](https://aaai.org/conference/aaai/?utm_source=chatgpt.com)

AAAI 的研究范围包括：

- Machine Learning
- Reinforcement Learning
- Planning
- Knowledge Representation
- Computer Vision
- NLP
- Robotics
- AI systems

所以它和 ICML / NeurIPS 类似：

> **属于 AI/ML 顶会，而不是 EDA 顶会。**

---

# 二十六、这几个会议不要混淆

你可以直接记下面这张表：

| Venue | 全称 | 类型 | 领域 | 和你课题关系 |
|---|---|---|---|---|
| **TCAD** | IEEE Transactions on Computer-Aided Design | 期刊 | EDA | ⭐⭐⭐⭐⭐ |
| **DAC** | Design Automation Conference | 会议 | EDA | ⭐⭐⭐⭐⭐ |
| **ICCAD** | IEEE/ACM International Conference on CAD | 会议 | EDA | ⭐⭐⭐⭐⭐ |
| **ASP-DAC** | Asia & South Pacific Design Automation Conference | 会议 | EDA | ⭐⭐⭐⭐⭐ |
| **DATE** | Design, Automation and Test in Europe | 会议 | EDA | ⭐⭐⭐⭐ |
| **ICML** | International Conference on Machine Learning | 会议 | ML | ⭐⭐⭐ |
| **NeurIPS/NIPS** | Neural Information Processing Systems | 会议 | AI/ML | ⭐⭐⭐ |
| **AAAI** | AAAI Conference on Artificial Intelligence | 会议 | AI | ⭐⭐～⭐⭐⭐ |

这里的星级不是论文质量排名，而是：

> **对于“功率 PCB 自动布局算法”这个具体课题的相关程度。**

---

# 二十七、真正应该关注的“论文搜索关键词”

你以后不要只搜：

> PCB Placement

太窄。

建议按照下面几个层次搜索。

### 第一层：PCB

```text
PCB Placement
PCB Routing
PCB Layout Optimization
Automatic PCB Layout
Automated PCB Design
PCB Component Placement
PCB Floorplanning
PCB Physical Design
PCB Placement Optimization
PCB Routability
```

---

### 第二层：功率 PCB

这个与你的课题更直接：

```text
Power PCB Placement
Power Electronics PCB Layout
Power Converter PCB Layout
Power Module Layout Optimization
Power PCB Optimization
Power Loop Layout
Power Electronics Layout Automation
Thermal-aware PCB Placement
EMI-aware PCB Placement
Signal Integrity-aware Placement
Power Integrity-aware Placement
```

---

### 第三层：EDA / VLSI

这是最重要的一层：

```text
Physical Design
EDA Physical Design
Partitioning
Floorplanning
Placement
Global Placement
Detailed Placement
Routability-driven Placement
Routing
Global Routing
Detailed Routing
Congestion-aware Placement
Timing-driven Placement
Power-aware Placement
Thermal-aware Placement
```

---

### 第四层：算法

```text
Simulated Annealing PCB Placement
MILP PCB Placement
ILP PCB Placement
Analytical PCB Placement
Force-directed PCB Placement
Graph-based PCB Placement
Reinforcement Learning PCB Placement
GNN PCB Placement
RL PCB Routing
AI for PCB Design
Machine Learning for EDA
```

---

# 二十八、特别推荐你理解“PCB ↔ VLSI”的对应关系

这是我认为你接下来最应该建立的知识框架：

| PCB | VLSI |
|---|---|
| Component | Cell / Macro |
| Component footprint | Cell geometry |
| Netlist | Netlist |
| Board outline | Die/Core |
| Functional block | Macro block |
| Partition | Partition |
| Floorplan | Floorplan |
| Component placement | Cell placement |
| Trace | Interconnect |
| Via | Via |
| Routing | Routing |
| Congestion | Routing congestion |
| DRC | Design-rule checking |
| Thermal | Thermal-aware design |
| SI/PI | Signal/Power integrity |
| PCB PnR | IC Place & Route |

这也是为什么你会看到：

> PCB paper 引用 VLSI placement paper。

这完全正常。

例如 SA-PCB 的参考文献中就包括经典的 TimberWolf placement/routing，以及 VLSI routability-driven placement、RePlAce 等工作。

---

# 二十九、我建议你的论文阅读顺序

如果你现在是**大四、第一次接触 EDA Physical Design**，千万不要直接从 ICML/NeurIPS 的 RL-EDA 论文开始。

建议：

### Level 0：PCB基础

先搞懂：

```text
Schematic
Netlist
Footprint
Pad
Pin
Net
Layer
Via
Trace
Board Outline
Keepout
DRC
```

---

### Level 1：PCB Layout

读：

**Abboud et al.**

> Mathematical methods for physical layout of printed circuit boards

[论文页面](https://www.researchgate.net/publication/226021976_Mathematical_methods_for_physical_layout_of_printed_circuit_boards_An_overview?utm_source=chatgpt.com)

---

### Level 2：经典 Placement

理解：

```text
Partition
    ↓
Floorplan
    ↓
Placement
    ↓
Routing
```

同时学习：

- graph partition
- simulated annealing
- quadratic placement
- force-directed placement
- nonlinear placement

---

### Level 3：PCB Placement

重点：

**NS-Place**

[NS-Place](https://arxiv.org/abs/2210.14259?utm_source=chatgpt.com)

然后：

**Analytical PCB Placement**

[Analytical PCB Placement 2026](https://www.sciencedirect.com/science/article/abs/pii/S016792602500224X?utm_source=chatgpt.com)

然后：

**MARS-Place**

[MARS-Place](https://www.sciencedirect.com/science/article/pii/S016792602600026X?utm_source=chatgpt.com)

---

### Level 4：Routing

学习：

```text
Maze Routing
Lee Algorithm
A*
Dijkstra
Global Routing
Detailed Routing
Rip-up & Reroute
Congestion
```

再看经典 VLSI routing survey。

---

### Level 5：开源代码

直接：

**SA-PCB + PcbRouter + PCB-PR-App**

[SA-PCB](https://github.com/The-OpenROAD-Project-Attic/SA-PCB?utm_source=chatgpt.com)

[OpenROAD PCB Project](https://cseweb.ucsd.edu/~kuan/?utm_source=chatgpt.com)

这一步非常重要。

---

### Level 6：AI for EDA

最后再进入：

```text
RL
 ↓
GNN
 ↓
RL + GNN
 ↓
LLM/Agent
```

对应：

```text
ICML
NeurIPS
AAAI
      ↕
DAC
ICCAD
ASP-DAC
TCAD
```

---

# 三十、如果把你的课题抽象成一个研究问题

我认为你现在可以把“功率 PCB 自动布局”先抽象成下面这个问题：

\[
\boxed{
\text{Given}
\quad
G=(V,E)
\quad
\text{and board constraints}
}
\]

求：

\[
\boxed{
P=\{(x_i,y_i,\theta_i,l_i)\}_{i=1}^{N}
}
\]

使得：

\[
\min
\underbrace{\alpha L}_{wirelength}
+
\underbrace{\beta C}_{congestion}
+
\underbrace{\gamma V}_{vias}
+
\underbrace{\delta T}_{thermal}
+
\underbrace{\epsilon E}_{electrical/EMI}
\]

同时满足：

\[
\text{No Overlap}
\]

\[
\text{Inside Board}
\]

\[
\text{DRC}
\]

\[
\text{Electrical Constraints}
\]

\[
\text{Thermal Constraints}
\]

这实际上就是一个：

> **Constraint-aware Multi-objective Combinatorial Optimization Problem**

而这句话基本就是你以后读论文时的“总纲”。

---

## 最后给你一个非常实际的判断

如果你以后搜论文，看到：

> **PCB + Placement + Simulated Annealing**

→ 这是传统方法。

看到：

> **PCB + Analytical Placement**

→ 这是连续优化/数学优化方向。

看到：

> **PCB + Routability-aware Placement**

→ **和你的课题非常相关。**

看到：

> **PCB + RL**

→ AI 自动布局/布线方向。

看到：

> **PCB + GNN**

→ 把 PCB netlist 建模成 graph，再做学习。

看到：

> **PCB + LLM/Agent**

→ 2025–2026 年比较新的方向，目前仍处于探索阶段。

看到：

> **Package/PCB + Placement/Routing + ASP-DAC/ICCAD/DAC/TCAD**

→ **优先阅读。**

尤其值得注意的是，ASP-DAC 2026 的 CFP 已经明确把 **“Package/PCB/3D-IC placement and routing”** 和 floorplanning、partitioning、placement、routing optimization 放在同一个 Physical Design research category 下。

所以你的课题其实并不是一个“偏应用、和 EDA 主流脱节”的方向，而是可以非常自然地进入：

**PCB Physical Design → Package/PCB Design Automation → VLSI Physical Design → AI for EDA**

这一整条研究路线。

### 我建议你接下来优先做的事情

如果你愿意按实习生培养路线推进，**下一阶段不要继续盲目搜论文**。最有效的是建立一份“PCB Placement 算法知识地图”，从 **Partition → Floorplan → Placement → Routing** 开始，把每一步的：

> **问题定义 → 数学模型 → 常用 Objective → 约束 → 经典算法 → 代表论文 → 开源代码 → Benchmark → Evaluation Metrics**

全部串起来。

这样之后你再看 NS-Place、MARS-Place、SA-PCB、RL-based PCB placement，就不会觉得每篇论文都在讲不同东西，而会发现它们其实是在解决**同一个 Physical Design 问题的不同子问题**。
