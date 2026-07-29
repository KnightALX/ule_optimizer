"""场景 2 验证：边界 4×4=16 档扫描。"""
from __future__ import annotations
from ule_opt.core.optimizer import scenario2, SCALE_LADDER


def run() -> bool:
    R0, C0 = 8800.0, 0.74e-15
    tau = R0 * C0
    N = 6
    C = [C0] + [3.0e-15] * N + [7.4e-15]
    Rw = [100.0] * (N + 1)
    Cw = [15e-15] * (N + 1)
    g = [4/3] * (N + 1)
    p = [1.0] * (N + 1)
    r_self = [R0 * 4/3] * (N + 1)

    res = scenario2(C, Rw, Cw, g, p, r_self, tau, R0, C0)
    if len(res.ladder) != len(SCALE_LADDER) ** 2:
        print(f"[FAIL] ladder 长度 {len(res.ladder)} != 16")
        return False
    s_in, s_out, d = res.best
    if s_in not in SCALE_LADDER or s_out not in SCALE_LADDER:
        print(f"[FAIL] best 缩放档越界")
        return False
    if d > res.delay_original * 1.05:
        print(f"[FAIL] best d 不优于原始")
        return False
    print(f"[PASS] scenario2: best (s_in={s_in}, s_out={s_out}, d={d:.4f})")
    return True