---
title: ULE 算法实现说明
date: 2026-07-29
tags: [ule, algorithm]
---

# ULE 算法实现说明

> [!note] 文档定位
> 详述 `ule_opt` 中实现的 ULE 公式链（论文 [ULE] L82–L216），
> 并把每个 Python 函数映射回论文公式号。

## 1. π-1 模型

`ule_opt/core/pi1.py::to_pi1(r_wire, c_wire) -> (R, C/2, C/2)`

把单段分布式 wire RC 折算为 π 集总。

## 2. ULE 单段延迟（论文式 4）

`ule_opt/core/logical_effort.py::delay_segment(...)`：

```
d = g_i * (h_i + h_wi) + (p_i + p_wi)
  = g_i * (C_next/C_i + C_wi/C_i) + (p_i + R_wi*(0.5 C_wi + C_next)/tau)
```

[ULE] L82–L85。

## 3. N 段路径总延迟（论文式 7）

`ule_opt/core/logical_effort.py::delay_path(...)`：

```
d = Σ d_i for i in 1..N
```

[ULE] L101–L105。

## 4. 最优尺寸（论文式 16）+ 松弛迭代

`ule_opt/core/logical_effort.py::relax(...)`：

```
C_i = √(C_{i-1} C_{i+1}) · √(1 + C_wi/C_{i+1}) · √(g_i / (g_{i-1} + R_wi-1 C_{i-1}/tau))
```

迭代 a/b/c 三步 [ULE] L181–L189，3 次达 5% 精度（论文 Table 1）。

## 5. 场景 1：内部 R/C 守恒重分配

`ule_opt/core/optimizer.py::scenario1(...)`：

1. 跑 `relax` 得到 C*
2. 等比例归一化保持总 C 守恒
3. 归一化后跑 1 次额外 `relax` 修复等努力
4. 重算 d
5. 映射 nfin = round((C_i/C0 - 1) / C_finger_unit)
6. 当 |ΔC|/C_orig > 20% 时输出 VT 提示

## 6. 场景 2：边界 4×4 缩放扫描

`ule_opt/core/optimizer.py::scenario2(...)`：

- 缩放档 = (0.7, 0.85, 1.0, 1.15)
- 16 组合全列出，选 d 最小档
- 复用场景 1 的内部 R/C

## 7. 有效 R/C 查表

`ule_opt/core/effective_rc.py::EffectiveRCLookup(...)`：

- YAML 驱动 + 內建默认 (INV/NAND/NOR/BUF)
- 用户可在 YAML 覆盖

## 8. 公式号 ↔ 函数映射

| 公式 | 行号 | 实现 |
|---|---|---|
| (1) | L44–L46 | `pi1.to_pi1` |
| (4) | L82–L85 | `logical_effort.delay_segment` |
| (7) | L101–L105 | `logical_effort.delay_path` |
| (16) | L168 | `logical_effort.relax` (迭代) |
| (19) | L210 | `logical_effort.compute_xopt` |
| (20) | L216 | `logical_effort.compute_xopt` (g=1) |
| 迭代 a/b/c | L181–L189 | `logical_effort.relax` (循环) |
