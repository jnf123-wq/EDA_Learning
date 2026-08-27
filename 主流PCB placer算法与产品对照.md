# PCB 自动布局：主流算法与商用产品综合调研文档

**方向：功率 PCB 自动布局算法设计与优化**  
**整理时间：2026 年 8 月**

---

## 〇、区分标准（本报告的核心约定）

为避免"算法"与"产品"混为一谈，本报告先做严格界定：

| 维度 | **算法（Algorithm）** | **产品（Product）** |
|---|---|---|
| 定义 | 可复现的求解方法（数学模型 / 搜索策略 / 学习范式） | 商用软件 / 云平台 / 可交付工具 |
| 载体 | 论文、开源代码、基准数据集 | GUI 软件、订阅服务、企业套件 |
| 边界 | 只解决"如何放置"这一步 | 覆盖布局→布线→验证→DFM→SI/PI/热的全流程 |
| 可验证性 | 在公开基准上可复现、可对比 | 多为黑盒，内部算法通常不公开 |
| 相互关系中 | 一个算法可被多个产品采用 | 一个产品可内嵌多个算法（且常不公开） |

> **一句话**：算法是"方法"，产品是"封装了方法 + 工程能力 + 数据/生态的商品"。下文的 **第一篇** 只讲算法，**第二篇** 只讲产品，**第三篇** 给出两者的对应关系。

---

# 第一篇：算法篇（严格限定为"算法 / 方法"）

## 1. 经典启发式算法（传统主流）

| 算法族 | 代表工作 | 核心思想 | 特点 / 局限 |
|---|---|---|---|
| **构造式 / 贪心** | — | 逐个选位置、选器件贪心摆放 | 快，但易陷局部最优，只做初始解 |
| **聚类 / Room 分组** | 商业工具 Room/Cluster 的思想来源 | 按功能/连接紧密度分组后成块摆放 | 工程直观，依赖分组质量 |
| **力导向（Force-directed）** | 经典 PCB/VLSI 布局 | 把连线视为弹簧，求受力平衡点 | 早期 PCB 离散元件布局常用，易重叠需二次合法化 |
| **模拟退火（SA）** | **TimberWolf**（Sechen & Sangiovanni-Vincentelli, IEEE JSSC, 1985） | 模拟退火最小化"能量"，允许跳出局部最优 | 经典、稳健，但大板收敛慢 |
| **划分法（Min-cut）** | Capo、Feng Shui、mPL | 递归二分划分，减少跨区线长 | 适合层次化，多作为全局布局框架 |
| **遗传 / 进化算法（GA）** | 功率电子 PCB 布局（ECCE）；SOGA 自组织遗传算法 | 种群 + 选择/交叉/变异，多目标搜索 | 能处理 EMC/多目标约束，速度是短板 |

> 说明：聚类、Room 分组这类"方法"既出现在论文里，也被商业产品实现——这里只按"方法"归类，其产品实现见第二篇。

## 2. 解析式算法（Analytical，当前学术主流，VLSI 传承）

解析式把布局写成**可微优化问题**（线长 + 密度），用数值优化求解，是现在质量/速度平衡最好的一派，也是 Cypress 的基座。

| 代表算法 | 年份/来源 | 核心思想 |
|---|---|---|
| **Gordian** | 经典 | 二次规划 + 递归划分 |
| **Kraftwerk** | 经典 | 二次/力导向全局布局 |
| **ePlace** | Cheng et al., TODAES 2014 | 把密度建模为**静电系统**，FFT + Nesterov 加速求解 |
| **RePlAce** | UCSD | 扁平解析非线性布局，**局部密度函数 + 动态步长**，优化线长与可布线性 |
| **elfPlace / eLfPlace** | TCAD 2021 | 每类资源独立静电系统 + 密度乘子向量，支持混合尺寸 |
| **DREAMPlace** | Lin et al., ICCAD 2019 | 把解析布局等价为**神经网络训练**，用 PyTorch 在 **GPU** 上求解 |
| **DREAMPlace 3.0** | ICCAD 2020 | 多静电系统 + 区域约束 + 自适应二次惩罚/熵注入，更稳健 |

### PCB 专用的解析式布局算法（与本课题最直接相关）

| 算法 | 来源 | 核心贡献 |
|---|---|---|
| **Cypress** | Cornell × NVIDIA，**ISPD 2025 最佳论文** | VLSI 思路 + GPU 加速；目标含**朝向感知线长 + 密度 + 网络交叉**；**位置与旋转角联合优化**（可微）；macro halo 合法化；处理间距/固定器件约束；数千器件；较商用 CPU 工具快 492×、质量提升 1–5.9×；配套开源基准 |
| **Modern Automatic PCB Placement with Complex Constraints** | NTU 姚文川组，**DAC 2024** | 面向**异质器件**的复杂约束（不同线宽、复杂间距）；最小外接矩形规范化形状；相似器件聚类；**沿功率电流流向布锚点**指导全局布局 |
| **An analytical approach and fine-tuning strategy for PCB placement optimization** | Zhao, Hu 等，Integration/VLSI Journal 2026 | PCB 专用三段式：全局布局 → **Hanan 网格合法化** → 保持拓扑的**fine-tuning** 提升可布线性 |
| **MARS-Place** | 武汉大学，Integration 2026 | **多阶段对齐精化**的 PCB 布局与布线联合优化 |

## 3. 学习式算法（ML / DL / RL / 生成式）

| 算法 | 来源 | 核心思想 |
|---|---|---|
| **AlphaChip（图放置方法）** | Google DeepMind，**Nature 2021** | **强化学习**做芯片宏模块布局，开源后因可复现性受质疑（学术争议，需谨慎引用） |
| **DeepPCB 的 RL 放置** | InstaDeep | 强化学习做 PCB 放置 + 布线，云原生 |
| **Quilter 的 RL 放置** | Quilter | **物理驱动强化学习**，多候选布局并行 |
| **PCBAgent** | CUHK，**ASPDAC 2025** | **RL agent + LLM agent** 协同做高密度 PCB 布局，优化 HPWL 与 NSLW，并与用户意图对齐 |
| **DQPlace** | IEEE 2026 | 改进 **Q-Learning（Double DQN）** 做宏模块布局，消除 Q 值高估 |
| **DiffPCB** | 2025 | **扩散模型**直接生成功率电子 PCB 布局（"硬件编译器"路线） |
| **DRL 假焊盘放置** | Expert Systems with Applications 2025 | 深度强化学习做 PCB 电镀假焊盘放置（实时奖励缓解稀疏奖励问题） |

---

# 第二篇：产品篇（严格限定为"商用 / 可用工具"）

> 以下只讨论"产品能做什么"，其内部算法大多不公开（黑盒），对应关系见第三篇。

## 1. 传统 EDA 巨头（桌面 / 企业套件）

| 产品 | 厂商 | 布局相关能力（产品功能） |
|---|---|---|
| **Cadence Allegro X AI / OrCAD X** | Cadence | Quickplace（按页/Room/网络快速放）、Room 聚类布局；**Allegro X AI 生成式布局**（约束驱动、并行多候选、SI/热/PI/DFM 感知）；配套 **Sigrity OptimizePI** 自动化去耦电容放置 |
| **Siemens Xpedition** | Siemens EDA | 层次化器件分组布局、**热感知布局**、BGA 逃逸布线、EMC 预测、设计复用 |
| **Altium Designer / Altium 365** | Altium | **Cluster Placer**（聚类）与 **Statistical Placer**（统计/连接密度）；365 AI Copilot 元件建议 |
| **Zuken CR-8000 Design Force** | Zuken | 规则驱动**去耦电容自动放置+布线**（按 PI 约束）、智能 Block 放置与 Breakout 布线、约束驱动布局 |

## 2. AI 原生 / 云端平台

| 产品 | 厂商 | 布局相关能力 |
|---|---|---|
| **Quilter** | Quilter | 物理驱动 RL 的端到端自动布局+布线，多候选，原生 Altium/Cadence/Siemens/KiCad 文件往返 |
| **DeepPCB** | InstaDeep × Google Cloud | RL 自动布局+布线，DRC 干净，支持 ≤1000 器件/2200 引脚 |
| **Flux.ai** | Flux | 云端协同 + 简单板 Auto-Layout 辅助 |
| **Circuit Mind** | Circuit Mind | AI 元件选型 + 规则驱动（偏布局上游） |
| **JITX** | JITX | 代码化/程序化约束驱动设计 |
| **Trace** | — | AI PCB 设计（布局辅助） |
| **Celus** | Celus | 自动元件选型 + 原理图生成（布局上游自动化） |

## 3. 开源 / 免费基线

| 工具 | 说明 |
|---|---|
| **KiCad + Freerouting** | 免费算法式布线；布局靠手工，社区插件（如 kicad-tools）提供热感知布局 |
| **DREAMPlace（开源）** | 可复现的 GPU 解析式布局基座 |
| **Cypress（开源基准）** | 研究代码 + 真实商用案例基准数据集 |

---

# 第三篇：算法 ↔ 产品对应关系

> 标注 ⚫ = 官方公开确认；◐ = 据公开资料推断；? = 黑盒未公开。

| 产品 | 可对应的算法族 | 公开程度 |
|---|---|---|
| Cadence Allegro（Quickplace/Room） | 聚类 / Room 分组 + 启发式 | ⚫（方法已知，实现不公开） |
| Cadence Allegro X AI | 生成式 / ML 布局（SI/热/PI/DFM 感知） | ◐ |
| Cadence Sigrity OptimizePI | 去耦电容放置的 PI 驱动优化 | ⚫（功能公开，算法不公开） |
| Siemens Xpedition | 层次化分组 + 热感知规则 | ⚫/◐ |
| Altium（Cluster/Statistical Placer） | 聚类（Cluster）/ 统计连接密度 | ⚫ |
| Zuken CR-8000 | 规则驱动的去耦电容放置 | ⚫ |
| Quilter | **强化学习（RL）** | ⚫ |
| DeepPCB | **强化学习（RL）** | ⚫ |
| Flux.ai Auto-Layout | 辅助式启发/ML | ◐ |
| KiCad + Freerouting | 算法式布线（布局非重点） | ⚫ |

> 结论：**能明确归因到具体算法的，只有学术开源工作（Cypress、DREAMPlace、AlphaChip 等）与公开声明 RL 的 Quilter/DeepPCB；传统 EDA 巨头内部多为黑盒，只暴露"功能"而不暴露"算法"。**

---

# 第四篇：对"功率 PCB 自动布局"课题的启示

1. **算法路线选择**：
   - 追求**质量 + 可扩展** → 解析式（ePlace/DREAMPlace 系 → Cypress 的 PCB 化），这是当前学术主流，且 Cypress 已证明在 PCB 上可行。
   - 追求**多目标 / 约束复杂**（EMC、热、电流环路）→ 进化算法（GA）或强化学习（DeepPCB/Quilter/PCBAgent 范式）。
   - 追求**数据驱动生成** → DiffPCB 扩散模型路线（尚早期）。

2. **核心空白点（创新机会）**：现有主流算法目标多为**线长 + 密度 + 可布线性**；**商用产品**加入了 SI/热/PI/DFM，但都是黑盒。**把功率特有目标（电流环路面积、去耦电容邻近度、热扩散、EMI）显式建模进解析式目标函数**，是 Cypress 等开源基座可做的增量创新，也是本课题的差异化切入点。

3. **评估口径**：不能只用线长/运行时间（学术指标），要加入功率板特有的**环路面积、EMI、热、去耦邻近度**（工程指标），并与 KiCad/Freerouting 免费基线和 Quilter/DeepPCB 免费层做对照。

4. **严格区分的实践意义**：写文献综述/开题时，**"算法"应引论文与开源代码，"产品"应引官方文档与评测**；二者不要在同一维度比较（例如"把 Cypress 和 Cadence 直接比质量"不成立——前者是可嵌入算法，后者是黑盒成品）。

---

### 主要参考来源
- ePlace（Cheng et al., TODAES 2014）；RePlAce（UCSD）；elfPlace/eLfPlace（TCAD 2021）
- DREAMPlace / DREAMPlace 3.0（Lin et al., ICCAD 2019/2020）
- Cypress（Zhang et al., ISPD 2025 Best Paper，Cornell × NVIDIA）
- Modern Automatic PCB Placement with Complex Constraints（Tsou et al., DAC 2024，NTU）
- An analytical approach and fine-tuning strategy for PCB placement optimization（Zhao, Hu et al., Integration 2026）
- MARS-Place（Wuhan University, Integration 2026）
- AlphaChip / A graph placement methodology for fast chip design（Mirhoseini, Goldie et al., Nature 2021）
- PCBAgent（CUHK, ASPDAC 2025）；DQPlace（IEEE 2026）；DiffPCB（2025）
- 商用产品官方文档与公告：Cadence、Siemens EDA、Zuken、Altium、Quilter、DeepPCB/InstaDeep、Flux.ai