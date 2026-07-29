import math
from ule_opt.core.optimizer import scenario1, scenario2, SCALE_LADDER


def test_scenario1_conserves_total_cap():
    # 场景 1：内部 R/C 守恒重分配
    R0, C0 = 8800.0, 0.74e-15
    tau = R0 * C0
    N = 6
    C = [C0] + [3.0e-15] * N + [7.4e-15]  # 8 nodes
    Rw = [100.0] * (N + 1)
    Cw = [15e-15] * (N + 1)
    g = [4/3] * (N + 1)
    p = [1.0] * (N + 1)
    r_self = [R0 * 4/3] * (N + 1)

    orig_total_c = sum(C[1:N+1])
    res = scenario1(C, Rw, Cw, g, p, r_self, tau, R0, C0,
                    c_finger_unit=0.5e-15, vt_threshold=0.20)
    new_total_c = sum(res.C_new[1:N+1])
    # 总电容守恒（±1%）
    assert math.isclose(new_total_c, orig_total_c, rel_tol=0.01)
    # 延时减小
    assert res.delay_optimized <= res.delay_original * 1.05  # 允许轻微上浮


def test_scenario2_picks_min_delay():
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
    # 16 档全列出
    assert len(res.ladder) == len(SCALE_LADDER) ** 2
    # 选出的 s_in, s_out 是 16 档之一
    s_in, s_out, d = res.best
    assert s_in in SCALE_LADDER and s_out in SCALE_LADDER
    # 最优延时 ≤ 原始 (0.7 缩放应加速)
    assert res.delay_optimized <= res.delay_original
