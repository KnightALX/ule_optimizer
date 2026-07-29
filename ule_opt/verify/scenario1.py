"""场景 1 验证：内部 R/C 守恒重分配。

Task 5 修复后内部节点 = C[1:-1] = C[1:N]（其中 N=len(C)-1），
因此守恒断言用 sum(C[1:N])，与 optimizer.py 的 Step B/D-extra 一致。
"""
from __future__ import annotations
from ule_opt.core.optimizer import scenario1


def run(tol_pct: float = 1.0) -> bool:
    R0, C0 = 8800.0, 0.74e-15
    tau = R0 * C0
    N = 6
    C = [C0] + [3.0e-15] * N + [7.4e-15]
    Rw = [100.0] * (N + 1)
    Cw = [15e-15] * (N + 1)
    g = [4/3] * (N + 1)
    p = [1.0] * (N + 1)
    r_self = [R0 * 4/3] * (N + 1)

    orig_total = sum(C[1:N])
    res = scenario1(C, Rw, Cw, g, p, r_self, tau, R0, C0)
    new_total = sum(res.C_new[1:N])
    rel = abs(new_total - orig_total) / orig_total * 100
    if rel > tol_pct:
        print(f"[FAIL] total C 偏差 {rel:.2f}% > {tol_pct}%")
        return False
    print(f"[PASS] scenario1 (tol {tol_pct}%)")
    return True