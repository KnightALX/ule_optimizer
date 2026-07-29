"""论文 Table 1 验证。

基准：8 段 NAND + 0.1mm 中间线，论文 iter 5 收敛到
[1, 7.2, 18.2, 25.5, 27.9, 28.4, 27.6, 24.0, 10]（归一化到 C0=0.74fF）。
本工具用论文式 (16) 松弛迭代，容差 ±10%（已知与论文存在 ~1.7% 偏差）。
"""
from __future__ import annotations
from ule_opt.core.logical_effort import relax


def run(tol_pct: float = 10.0) -> bool:
    R0, C0 = 8800.0, 0.74e-15
    tau = R0 * C0
    C0_init = [0.74e-15, 0.74e-15, 1.48e-15, 2.22e-15, 2.96e-15, 3.7e-15,
               4.44e-15, 5.18e-15, 7.4e-15, 7.4e-15]
    N = len(C0_init) - 1
    Rw = [100.0] * N
    Cw = [15e-15] * N
    g = [4/3] * N
    C_final = relax(C0_init, Cw, g, Rw, tau, max_iter=5, tol=0.05)
    # 归一化到 C0
    norm = [c / C0 for c in C_final]
    expected = [1.0, 7.2, 18.2, 25.5, 27.9, 28.4, 27.6, 24.0, 10.0, 10.0]
    for i, (a, b) in enumerate(zip(norm, expected)):
        if b == 0:
            continue
        rel = abs(a - b) / b * 100
        if rel > tol_pct:
            print(f"[FAIL] node {i}: got {a:.2f}, expected {b:.2f}, dev {rel:.1f}%")
            return False
    print(f"[PASS] table1 (tol {tol_pct}%)")
    return True