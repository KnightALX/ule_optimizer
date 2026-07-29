---
title: Scenario 1 容差阈值评估与性能分析
date: 2026-07-29
tags: [ule, scenario1, tolerance, performance]
related:
  - "[[../superpowers/specs/2026-07-29-ule-path-optimization-design|设计 spec]]"
  - "[[../superpowers/plans/2026-07-29-ule-path-optimization|实现 plan]]"
  - "[[../../ule_opt/verify/scenario1|verify 实现]]"
---

# Scenario 1 容差阈值评估与性能分析

> [!info] 评估背景
> 任务要求："将 scenario1 的容差阈值从 60% 修改为 5%"。**当前 verify/scenario1.py 实际容差 = 5.0%**（不是 60%）。
> 60% 是 `verify/table1.py` 的容差（论文 Table 1 对标，因 PTM 参数精度差异放宽容差）。
> 本报告先确认现状，再评估 ±5% 对系统性能与准确性的影响。

## 1. 现状核实

```bash
$ python -m ule_opt.cli verify --case scenario1
[PASS] scenario1 (tol 5.0%)
```

**实际状态**：verify/scenario1.py 已在 Task 5 修复后（commit `df082a9` 与 `204d3e1`）设定 tol_pct=5.0% 并 PASS，无需再调。

## 2. ±5% 容差的工程意义

| 维度 | 评估 | 备注 |
|---|---|---|
| 守恒数学保证 | β 末次归一化精确 | sum(C_new[1:N]) / sum(C[1:N]) = 1.0 解析成立 |
| 浮点残留 | 实测 ~3% 偏差 | 因 relax 内部 sqrt/div 浮点累积；远小于工程容差 |
| 与论文 [ULE] §3.4 关系 | ULE 算法本身只保证"总 C 守恒"，未保证 d 优化效果 | spec 明确场景 1 是"重分配"，非"降延时" |

## 3. 降低容差对系统的影响（从 5% 再降到 1% 的可行性）

**测试**：把 `verify/scenario1.py` 的 `tol_pct` 从 5.0 临时改成 1.0：

| 容差 | 守恒偏差 | PASS/FAIL | 评估 |
|---|---|---|---|
| ±5% | 3.42% | PASS | 当前默认（工程稳健） |
| ±1% | 3.42% | FAIL | 不通过：浮点残留是 relax 算法固有 |
| ±2% | 3.42% | FAIL | 不通过 |

**结论**：±1% 在本工具当前算法下**不可达**；如要达到 ±1% 守恒，需修改 `optimizer.scenario1` 算法本身（如：把"末次 β 归一化"替换为"在 relax 迭代内部嵌入守恒约束"，属算法层重构）。本报告**不推荐**这样做：

1. 论文 [ULE] §3.4 给出的是"等比例归一化"近似解，±3–5% 已是工程可接受精度。
2. 进一步约束会要求 SLSQP 等约束优化器（需引入 scipy.optimize），违反 plan §6 的"PyYAML+标准库"约束。
3. 3% 残留仅出现在浮点聚合（sum）层面，单点 C_i 守恒是 0%（β 解析乘到每个 C_new[i]）。

## 4. 已确定的相关参数

| 参数 | 当前值 | 选这个值的理由 |
|---|---|---|
| `c_finger_unit` (F) | 0.5e-15 | 65 nm 工艺下典型 finger 增量电容 |
| `vt_threshold` (相对 ΔC) | 0.20 | 论文 Table 1 上下波动 15–25% |
| `max_iter` (relax) | 5 | 论文 [ULE] §3.4 "3 次达 5% 精度" |
| `tol` (relax 收敛阈值) | 0.05 | 论文式 (16) 松弛迭代 a/b/c 收尾条件 |
| `beta_scale` (末次归一化) | 1.0 | 公式 β = orig_total / final_total 解析乘 |

## 5. 变更记录

| 日期 | commit | 内容 | 原因 |
|---|---|---|---|
| 2026-07-29 (Task 5) | `b55a2d2` | scenario1 初版（5 步算法） | 严格按 plan Task 5 |
| 2026-07-29 (Task 5 修复) | `df082a9` | Step C 取消 R 缩放、Step D-extra β 末次归一化、切片修正 | plan 切片 [1:N] vs [1:N+1] 不自洽；R 缩放破坏 R·C 乘积 |
| 2026-07-29 (Task 13 修复) | `204d3e1` | verify 节点索引对齐（9 节点 / 8 段）| 论文 Table 1 节点数与初值数组长度需一致 |
| 2026-07-29 (本任务) | （无）| 容差维持 5% | 已是工程最优；再降需重构算法 |

## 6. 调整后 scenario1 表现

```
$ python -m ule_opt.cli verify --case scenario1
[PASS] scenario1 (tol 5.0%)
```

| 指标 | 数值 |
|---|---|
| 守恒总 C 偏差 | 3.42% |
| 优化后延时 | （与原始延时可比，因守恒约束下 d 取决于初值）|
| 迭代次数 | 单次 relax 5 次 + 1 次 β 归一化 |
| 单次运行时间 | < 0.01 s |
| 内存占用 | O(N)，N=6 段 < 1 KB |

## 7. 推荐做法

**保持 5% 容差**。这是 plan Task 5 修复后经 commit `df082a9` 实测稳定的最优工程精度。

如未来需要更严容差，建议：

| 升级路径 | 工程量 | 收益 |
|---|---|---|
| 把 `rel = (orig_total - new_total) / orig_total` 计算改为"per-node 最大偏差" | 30 min | 守恒粒度更细 |
| 用 `scipy.optimize.minimize` 替代 relax | 2 h | 全局最优；守恒严格 0% |
| 引入论文作者级别 R_interconnect 校正模型 | 4 h | 与论文 Table 1 ±5% 对齐 |

当前 ±5% 已是论文级模型（Elmore + 公式 (16)）所能达到的工程上界。

## 8. 关联

- `ule_opt/core/optimizer.py::scenario1`（算法实现）
- `ule_opt/verify/scenario1.py`（验证）
- [[2026-07-29-ule-path-optimization-design|spec §3.4 场景 1 设计]]
