---
title: ULE Path Optimizer
date: 2026-07-29
tags: [ule, sram, python, cli]
---

# ULE 路径寻优 CLI 工具

> [!info] 关于本项目
> - 实现论文 [Unified Logical Effort](file:///d:/workspace/project/logic_effort/Unified_Logical_Effort_A_Method_for_Delay.pdf) 的 SRAM 关键路径寻优
> - 严格遵循 [ULE] Section IV (式 1–20) + 松弛迭代
> - CLI 工具，支持 CDL/SPEF 解析 + 场景 1/2 寻优

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 1. 生成 YAML 模板
python -m ule_opt.cli template configs/my.yaml

# 2. 跑寻优
python -m ule_opt.cli run -c configs/my.yaml

# 3. 验证
python -m ule_opt.cli verify --case table1
python -m ule_opt.cli verify --case scenario1
python -m ule_opt.cli verify --case scenario2

# 4. 跑测试
pytest
```

## 命令

| 命令 | 作用 |
|---|---|
| `run --config` | 跑寻优，输出 reports/<ts>/ |
| `verify --case` | 跑论文 Table 1 或场景 1/2 验证 |
| `template` | 输出 YAML 模板 |

## 输出报告

`reports/<时间戳>-<case>/<case>.md` 与 `.json`：
- 原始 / 优化后延时
- 节点级 nfin / VT 调整建议
- 缩放档扫描结果（场景 2）

## 关联

- [[2026-07-29-ule-path-optimization-design|设计 spec]]
- [[2026-07-29-ule-path-optimization|实现 plan]]
- [[../../ALGORITHM|算法说明]]
