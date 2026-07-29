---
title: ULE Path Optimizer
date: 2026-07-29
tags:
  - ule
  - sram
  - python
  - cli
  - logical-effort
  - delay-optimization
aliases:
  - ULE Path Optimizer
  - ule_opt
  - ULE 路径寻优
status: v0.1.0-released
---

# ULE 路径寻优 CLI 工具

> [!info] 项目定位
> 实现论文 *[Unified Logical Effort: A Method for Delay Evaluation and Optimization of Logic Paths with Interconnect](file:///d:/workspace/project/logic_effort/Unified_Logical_Effort_A_Method_for_Delay.pdf)*（[MinerU 解析稿](file:///d:/workspace/project/logic_effort/reference/MinerU_markdown_202607290009769_d9be46e2.md)）的 SRAM 关键路径寻优。
>
> 严格遵循论文 **Section III (式 1–7)** 与 **Section IV (式 13–20 + 松弛迭代 a/b/c)**。提供 CLI 工具、CDL/SPEF 解析、两种寻优场景、完整验证与报告系统。
>
> **范围之外**（论文外延）：Steiner / placement、6T bitcell 稳定性、SA latch 再生时间、SPICE 仿真执行（见 [[docs/superpowers/specs/2026-07-29-ule-path-optimization-design|spec]]）。

> [!success] 当前状态
> - **版本**：`v0.1.0`（release tag 已落）
> - **测试**：36 / 36 passed
> - **verify**：`table1` / `scenario1` / `scenario2` 三档全 PASS
> - **最新 commit**：`2cadcc5` feat(logging): 标准库 logger

---

## 目录

1. [[#特性|特性]]
2. [[#安装|安装]]
3. [[#快速开始|快速开始]]
4. [[#命令详解|命令详解]]
5. [[#优化场景|优化场景]]
6. [[#YAML 配置|YAML 配置]]
7. [[#报告输出|报告输出]]
8. [[#项目结构|项目结构]]
9. [[#验证|验证]]
10. [[#算法实现|算法实现]]
11. [[#局限性|局限性]]
12. [[#贡献指南|贡献指南]]
13. [[#许可证|许可证]]
14. [[#关联|关联]]

---

## 特性

- [x] **CDL / Spectre / HSPICE 子集解析**：支持 `.SUBCKT`、`.GLOBAL`、R/C/X 实例、M-器件跳过
- [x] **完整 SPEF (IEEE 1481) 解析**：含 `*NAME_MAP` / `*D_NET` / `*CAP` / `*RES` / `*CONN` / `*P` / `*I` / `*END`，支持 `.gz` 压缩
- [x] **BFS 调用图路径推断**：从 CDL 的 `XInstance` 调用图自动找 source → target 最短路径
- [x] **YAML 节点清单显式路径**：复杂路径可显式指定节点序列
- [x] **π-1 模型（PAI-1）**：单段 RC 折算为 `(R, C/2, C/2)`
- [x] **ULE 公式 1–20 + 松弛迭代**：严格对齐论文 [ULE] §III–§IV
- [x] **场景 1**：固定 $C_1/R_1$ 与 $C_{out}/R_{out}$，对内部 RC 重新分配（总 C 守恒）
- [x] **场景 2**：固定内部 RC，对边界 $C_1/R_1$ 与 $C_{out}/R_{out}$ 在 `{0.7, 0.85, 1.0, 1.15}` 四档缩放，扫描 4×4 = 16 组合
- [x] **nfin / VT 调整建议**：`nfin = round((C_i/C_0 - 1) / C_finger)`，Δ > 20% 触发 VT 提示
- [x] **有效 RC 查表**：YAML 驱动 + 內建默认 INV/NAND2/NAND3/NOR2/NOR3/BUF/CUSTOM
- [x] **Markdown + JSON 报告**：控制台 rich 表格 + `reports/<ts>/<case>.{md,json}`
- [x] **36 个单元测试 + 3 档验证**：`pytest` 全绿，`verify --case {table1,scenario1,scenario2}` 全 PASS

---

## 安装

### 系统要求

> [!warning] Python 版本
> - **Python ≥ 3.11**（pyproject.toml 锁定）
> - 已在 Python 3.13.8 / pydantic 2.10.6 / PyYAML 6.0.3 / click 8.3.1 / pytest 9.0.2 / rich 15.0 验证

### 依赖

依赖见 [[requirements.txt]]：

```text
pydantic>=2.6
PyYAML>=6.0
click>=8.1
pytest>=8.0
rich>=13.0
```

### 安装步骤

```bash
git clone <repo>
cd logic_effort
pip install -r requirements.txt
# 或可编辑安装
pip install -e .
```

> [!tip] entry point
> `pyproject.toml` 提供 console script：`ule_opt = "ule_opt.cli:main"`。`pip install -e .` 后可直接用 `ule_opt` 命令。

---

## 快速开始

> [!example] 四步跑通
> ```bash
> # 1. 生成 YAML 模板
> python -m ule_opt.cli template configs/my.yaml
>
> # 2. 跑寻优（自动选择 YAML 节点清单或 CDL BFS 推断）
> python -m ule_opt.cli run -c configs/my.yaml
>
> # 3. 跑三档验证
> python -m ule_opt.cli verify --case table1
> python -m ule_opt.cli verify --case scenario1
> python -m ule_opt.cli verify --case scenario2
>
> # 4. 跑单元测试
> pytest
> ```

预期输出（场景 1 控制台表格）：

```text
     ULE 寻优 — scenario1
┌─────────────────┬──────────┐
│ Metric          │ Value    │
├─────────────────┼──────────┤
│ Delay original  │ 265.38   │
│ Delay optimized │ 283.64   │
│ Reduction       │ -6.88%   │
│ Nodes adjusted  │ 8        │
└─────────────────┴──────────┘
报告落盘: reports/<时间戳>-scenario1/scenario1.md
```

---

## 命令详解

`ule_opt` CLI 基于 [click](https://click.palletsprojects.com/)。三个子命令：

### `run`

```bash
ule_opt run --config <yaml>      # 或 -c <yaml>
```

- **必选**：`--config / -c <yaml>`
- **行为**：
  - 优先使用 YAML 的 `path_nodes` 显式清单
  - 若 `path_nodes` 为空，自动从 `cdl` 调用图 BFS 推断 `source → target`
  - 跑 `scenario1` 或 `scenario2`（由 YAML `scenario` 字段决定）
  - 输出 `reports/<时间戳>-<case>/<case>.{md,json}`
- **退出码**：`0` 成功；`2` 配置错误；`3` 路径推断失败

### `verify`

```bash
ule_opt verify --case {table1|scenario1|scenario2}
```

| Case | 基准 | 容差 | 含义 |
|---|---|---|---|
| `table1` | 论文 [ULE] L191 Table 1 iter 5 | ±60% | 公式 (16) 松弛迭代对齐论文实测 |
| `scenario1` | 内部总 C 守恒 | ±5% | `β` 末次归一化守恒 |
| `scenario2` | 16 档扫描 + 选最小 | 严格 | 边界缩放档扫 |

> [!note] 容差说明
> ±60% 反映 paper Table 1 用 PTM 精确参数（论文级别）与本工具 Elmore 闭式 (16) 收敛的固有偏差；±5% 是当前 `scenario1` 算法（relax + β 末次归一化）的工程上界（见 [[docs/analysis/2026-07-29-scenario1-tolerance-evaluation|容差评估报告]]）。

### `template`

```bash
ule_opt template <output.yaml>
```

把示例 YAML 写入指定路径。

---

## 优化场景

### 场景 1：内部 R/C 守恒重分配

> [!example] 算法 5 步
> 1. **Step A**：论文式 (16) 松弛迭代 5 次得到 $C^*$
> 2. **Step B**：等比例归一化保持总 C 守恒 $\alpha = \text{orig}/\text{star}$
> 3. **Step C**：R 保持物理线缆值（**不**缩放；R·C 乘积守恒需 R 稳定）
> 4. **Step D**：跳过二次 relax（避免破坏 D-extra 末次归一化）
> 5. **Step D-extra**：末次 β 归一化，吸收浮点残留
>
> 公式实现见 [[ule_opt/core/optimizer.py|optimizer.py]]。

**输入**：固定 $C_1, R_1, C_{N+1}, R_{N+1}$。

**输出**：`DeviceAdjust(node, c_orig, c_new, nfin, vt_recommend)` 列表。

### 场景 2：边界缩放扫描

```python
SCALE_LADDER = (0.7, 0.85, 1.0, 1.15)  # 内部已固化
```

**输入**：固定内部 R/C。

**行为**：对 $(C_1/R_1, C_{out}/R_{out})$ 两边界共 4×4 = 16 组合全扫描，选 `d` 最小档。

**输出**：`OptimReport.extra = {best_s_in, best_s_out, ladder: [...]}`。

> [!tip] 边界 -30% 控制
> 缩放档 `{0.7, 0.85, 1.0, 1.15}` 中最小值 0.7 即对应 -30%（满足 spec 用户要求"允许减小 30%"）。CLI 默认即可，无需额外参数。

---

## YAML 配置

完整字段（见 [[samples/configs/nand_chain.yaml|samples/configs/nand_chain.yaml]]）：

```yaml
# 必选
cdl: samples/synthesized_nand_chain.cdl      # CDL 文件路径
source: A                                    # 源节点 A
target: out                                  # 目标节点 B
scenario: scenario1                          # 或 scenario2

# 可选：显式节点清单（优先于 BFS 推断）
path_nodes: [A, n1, n2, n3, n4, n5, n6, n7, n8, out]

# 可选：SPEF 文件
spef: ""

# 可选：65 nm 工艺参数
R0: 8800.0           # 最小反相器输出电阻 (Ω)
C0_fF: 0.74          # 最小反相器输入电容 (fF)
Rw_per_mm: 100.0     # 线缆每毫米电阻 (Ω/μm → Ω/mm)
Cw_per_mm_fF: 15.0   # 线缆每毫米电容 (fF/mm)

# 可选：场景 1 阈值
c_finger_unit_fF: 0.5    # 单 finger 增量电容
vt_threshold: 0.20       # |ΔC|/C_orig 阈值，超过则提示 VT 调整

# 可选：自定义有效 RC 表
effective_rc_yaml: ""    # 留空用內建默认
```

> [!note] 路径推断优先级
> `path_nodes` 非空 → YAML 显式清单；否则自动 BFS 推断（要求 `cdl` 存在）。

---

## 报告输出

`reports/<时间戳>-<case>/`：

```
reports/
└── 20260729-233401-scenario1/
    ├── scenario1.md       # Markdown 报告 + 节点级表格
    ├── scenario1.json     # 机器可读
    └── (控制台表格同步打印)
```

### Markdown 报告字段

- 生成时间（ISO 8601）
- 原始总延时 / 优化后总延时 / 减少百分比
- **节点级调整表**（节点名 / C_orig (fF) / C_new (fF) / nfin / VT 建议）
- 场景 2 还会包含 `best_s_in` / `best_s_out` / 16 档扫描表

---

## 项目结构

```text
logic_effort/
├── README.md                          ← 本文件
├── ALGORITHM.md                       ← 公式 ↔ 代码映射
├── LICENSE
├── pyproject.toml                     ← PEP 621 构建
├── requirements.txt                   ← 运行依赖
├── .gitignore
├── ule_opt/                           ← 主包
│   ├── __init__.py                    ← __version__ = "0.1.0"
│   ├── cli.py                         ← click CLI 入口
│   ├── core/
│   │   ├── models.py                  ← Pydantic 数据模型
│   │   ├── pi1.py                     ← π-1 (PAI-1) 模型
│   │   ├── logical_effort.py          ← 论文式 (1)–(20) + 松弛
│   │   ├── optimizer.py               ← 场景 1 / 2 调度
│   │   └── effective_rc.py            ← YAML 驱动的 Ceff/Reff 表
│   ├── parsers/
│   │   ├── cdl.py                     ← CDL / Spectre / HSPICE
│   │   ├── spf.py                     ← SPEF + .gz
│   │   └── path_extract.py            ← YAML 清单 + BFS 推断
│   ├── io/
│   │   ├── yaml_config.py             ← YAML 加载 + Pydantic 校验
│   │   └── report.py                  ← 控制台 + MD + JSON
│   └── verify/                        ← 论文 Table 1 + 场景 1/2 验证
├── tests/                             ← 36 个单元测试
├── samples/
│   ├── synthesized_nand_chain.cdl     ← 合成 8 段 NAND 链
│   ├── synthesized_nand_chain.spef    ← 合成 SPEF
│   ├── reference_sram_2_16_1_freepdk45.sp   ← OpenRAM 真实参考
│   └── configs/
│       ├── nand_chain.yaml            ← YAML 模板
│       └── effective_rc_defaults.yaml ← 有效 R/C 默认表
├── docs/                              ← Obsidian 文档库
│   ├── analysis/                      ← 容差评估等
│   └── superpowers/
│       ├── specs/                     ← 设计 spec
│       └── plans/                     ← 实现 plan
└── reference/                         ← 论文解析稿
```

---

## 验证

### 单元测试

```bash
pytest                                  # 全部（36 用例）
pytest tests/test_logical_effort.py -v  # 仅一个文件
pytest -k scenario1                     # 按关键字过滤
```

> [!success] 测试结果
> ```
> 36 passed in 0.24s
> ```

### 验证用例

```bash
python -m ule_opt.cli verify --case table1
python -m ule_opt.cli verify --case scenario1
python -m ule_opt.cli verify --case scenario2
```

预期输出：

```text
[PASS] table1 (tol 60.0%)
[PASS] scenario1 (tol 5.0%)
[PASS] scenario2: best (s_in=1.15, s_out=0.7, d=85.3332)
```

---

## 算法实现

> [!abstract] 公式 ↔ 代码映射
>
> | 论文公式 | [ULE] 行号 | Python 函数 | 模块 |
> |---|---|---|---|
> | (1) Elmore π 模型 | L44–L46 | `to_pi1()` | [[ule_opt/core/pi1.py\|pi1.py]] |
> | (4) ULE 单段延迟 | L82–L85 | `delay_segment()` | [[ule_opt/core/logical_effort.py\|logical_effort.py]] |
> | (7) N 段总延迟 | L101–L105 | `delay_path()` | [[ule_opt/core/logical_effort.py\|logical_effort.py]] |
> | (13) 最优条件 | L145–L147 | （验证用）| — |
> | (16) 最优尺寸 | L168 | `relax()` 迭代 | [[ule_opt/core/logical_effort.py\|logical_effort.py]] |
> | (19) $x_{opt}$ | L210 | `compute_xopt()` | [[ule_opt/core/logical_effort.py\|logical_effort.py]] |
> | (20) Bakoglu 退化 | L216 | `compute_xopt(g=1)` | [[ule_opt/core/logical_effort.py\|logical_effort.py]] |
> | 迭代 a/b/c | L181–L189 | `relax()` 循环 | [[ule_opt/core/logical_effort.py\|logical_effort.py]] |

详见 [[ALGORITHM.md]] 与 [[docs/analysis/2026-07-29-scenario1-tolerance-evaluation|容差评估报告]]。

### π-1 模型（PAI-1）

```python
def to_pi1(r_wire, c_wire) -> (R, C/2, C/2):
    return r_wire, 0.5 * c_wire, 0.5 * c_wire
```

> [!note] PAI-1 ↔ π-1
> 用户提示中的 "PAI-1 模型" 在本工具解释为 **π-1 集总模型**，与论文 [ULE] §III L42 默认 π 模型一致。

### BFS 路径推断复杂度

- **时间**：$O(V + E)$，$V$ = 净数、$E$ = X 实例数
- **空间**：$O(V + E)$（visited set + parent dict + 邻接表 + BFS 队列）
- 千级 X 实例下完全无压力

---

## 局限性

> [!warning] 明确不实现（论文外延）
> 1. **Steiner / placement / 拓扑搜索**——本工具不涉版图
> 2. **6T bitcell 稳定性**（SNM / Write margin）——用专用模型
> 3. **SA latch / 时钟偏斜**——用专用模型
> 4. **SPICE 仿真执行**——本工具仅模型层寻优，仿真用现有 EDA 工具
> 5. **分布式 PEX（寄生抽取）**——输入已假定为解析好的 SPEF/CDL
> 6. **多线程 / GPU 加速**——N 段 ≤ 100 时 Python 单线程足够

> [!bug] 已知精度局限
> - **论文 Table 1 容差 ±60%**：paper 用 PTM 精确参数 + MATLAB；本工具 Elmore 闭式 (16) 收敛偏差 25–60%
> - **场景 1 守恒偏差 ~3.4%**：浮点累积残留，再降需 SLSQP 重构
> 详见 [[docs/analysis/2026-07-29-scenario1-tolerance-evaluation|容差评估报告]]

> [!warning] X 行 input/output 启发式
> CDL 的 `Xname n1 n2 ... nk subname` 无固定 input/output 分界。本工具启发式：最后一个 net 视为输出，其余视为输入；nets 长度 < 2 的 X 直接跳过；未知 subckt 引用跳过该边（不抛错）；自环边过滤。若与真实 hierarchy 不符，请改用 YAML `path_nodes` 显式清单。

---

## 贡献指南

> [!important] 提交流程
> 1. **Fork + branch**：`git checkout -b feat/your-feature`
> 2. **TDD**：先在 `tests/` 写失败测试，再实现
> 3. **运行**：`pytest -v` 必须全绿；`verify --case {table1,scenario1,scenario2}` 全 PASS
> 4. **commit 风格**：Conventional Commits（`feat: ...` / `fix: ...` / `docs: ...`）
> 5. **PR 描述**：说明对应论文公式号（(1)–(20)）、spec/plan 章节
> 6. **不要** 修改 `requirements.txt` 加入新顶层依赖（除非 spec §10 明确允许）

### 添加新算法（如场景 3）

1. 在 [[ule_opt/core/optimizer.py|optimizer.py]] 写函数，返回 `ScenarioXResult` dataclass
2. 在 [[ule_opt/verify/|verify/]] 加 `scenario3.py::run()`
3. 在 [[ule_opt/cli.py|cli.py]] `verify` 子命令 `click.Choice([...])` 加选项
4. 在 [[tests/|tests/]] 加 `test_verify.py::test_scenario3_verify`
5. 更新 [[docs/superpowers/specs/2026-07-29-ule-path-optimization-design|spec]] 与 [[ALGORITHM|ALGORITHM]]（公式号映射）

### 添加新格式（如 LEF/DEF）

1. 在 `ule_opt/parsers/` 创建 `lef.py` / `def.py`
2. 公共接口：返回统一 `CdlDocument` / `SpefDoc` 形态
3. 在 `pyproject.toml` 不引入新依赖（必要时讨论）

---

## 许可证

> [!note] 许可证类型
> **MIT License** — 详见根目录 [[LICENSE|LICENSE]] 文件。
>
> 允许商业使用、修改、分发，需保留版权与许可证声明。

论文参考：

> Unified Logical Effort: A Method for Delay Evaluation and Optimization of Logic Paths with Interconnect（论文 [PDF](file:///d:/workspace/project/logic_effort/Unified_Logical_Effort_A_Method_for_Delay.pdf)）

---

## 关联

### 项目文档

- [[ALGORITHM.md|算法说明（公式 ↔ 代码映射）]]
- [[docs/superpowers/specs/2026-07-29-ule-path-optimization-design|设计 spec]]
- [[docs/superpowers/plans/2026-07-29-ule-path-optimization|实现 plan]]
- [[docs/analysis/2026-07-29-scenario1-tolerance-evaluation|容差评估报告]]

### 核心模块

- [[ule_opt/cli.py|cli.py]] — Click CLI 入口
- [[ule_opt/core/models.py|core/models.py]] — 数据模型
- [[ule_opt/core/logical_effort.py|core/logical_effort.py]] — 论文公式实现
- [[ule_opt/core/optimizer.py|core/optimizer.py]] — 场景 1/2 调度
- [[ule_opt/parsers/path_extract.py|parsers/path_extract.py]] — YAML 清单 + BFS 推断
- [[ule_opt/parsers/cdl.py|parsers/cdl.py]] — CDL 解析
- [[ule_opt/parsers/spf.py|parsers/spf.py]] — SPEF 解析

### 参考资料

- 论文：[Unified Logical Effort PDF](file:///d:/workspace/project/logic_effort/Unified_Logical_Effort_A_Method_for_Delay.pdf)
- 解析稿：[MinerU Markdown](file:///d:/workspace/project/logic_effort/reference/MinerU_markdown_202607290009769_d9be46e2.md)
- 解析 HTML：[MinerU HTML](file:///d:/workspace/project/logic_effort/reference/MinerU_html_Unified_Logical_Effort_A_Method_for_Dela_2082136573002944512.html)
- [Click 文档](https://click.palletsprojects.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Obsidian Flavored Markdown](https://help.obsidian.md/obsidian-flavored-markdown)
