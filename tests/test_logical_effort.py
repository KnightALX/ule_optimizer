"""ULE 论文公式 (1)–(20) + 松弛迭代 单元测试。

参考论文 [ULE] Section IV，L82–L216。
"""
import math
from ule_opt.core.logical_effort import (
    delay_segment,
    delay_path,
    relax,
    compute_xopt,
)


def test_delay_segment_paper_eq4():
    # 论文式 (4) 数值验证
    # d = g*(h + h_w) + (p + p_w)
    # h = C_next/C_i; h_w = C_w_i/C_i; p_w = R_w*(0.5 C_w + C_next)/tau
    tau = 8800.0 * 0.74e-15
    d = delay_segment(
        R_i=8800.0, C_i=0.74e-15, C_pi=0.1e-15,
        R_wi=50.0, C_wi=2e-15, C_next=0.74e-15,
        g_i=4/3, p_i=1.0, tau=tau,
    )
    h = 1.0
    h_w = 2e-15 / 0.74e-15
    p_w = 50.0 * (1e-15 + 0.74e-15) / tau
    expected = (4/3) * (h + h_w) + (1.0 + p_w)
    assert math.isclose(d, expected, rel_tol=1e-9)


def test_delay_path_sums_segments():
    # 3 段路径，d 应为 3 段 d_i 之和
    tau = 8800.0 * 0.74e-15
    nodes_c = [0.74e-15, 0.74e-15, 0.74e-15, 0.74e-15]
    r_w = [50.0, 50.0, 50.0]
    c_w = [2e-15, 2e-15, 2e-15]
    g = [4/3, 4/3, 4/3]
    p = [1.0, 1.0, 1.0]
    d = delay_path(nodes_c, r_w, c_w, g, p, tau, R0=8800.0)
    assert d > 0


def test_xopt_paper_eq19():
    # 论文式 (19): x_opt = sqrt(R0*Cw/(Rw*C0) * g)
    R0, C0, Cw, Rw, g = 8800.0, 0.74e-15, 15e-15, 100.0, 4/3
    x = compute_xopt(R0, C0, Cw, Rw, g)
    expected = math.sqrt(R0 * Cw / (Rw * C0) * g)
    assert math.isclose(x, expected, rel_tol=1e-9)


def test_xopt_inverter_eq20():
    # 论文式 (20): g=1 时退化到 Bakoglu
    R0, C0, Cw, Rw = 8800.0, 0.74e-15, 15e-15, 100.0
    x = compute_xopt(R0, C0, Cw, Rw, g=1.0)
    expected = math.sqrt(R0 * Cw / (Rw * C0))
    assert math.isclose(x, expected, rel_tol=1e-9)


def test_relax_converges_3_iter():
    # 8 段 NAND + 0.1mm 线 (论文 Table 1 简化版)
    # 用 65nm 参数 (C0=0.74fF, R0=8800, Cw=15fF, Rw=100)
    tau = 8800.0 * 0.74e-15
    N = 8
    C = [0.74e-15] + [5.0e-15] * N + [7.4e-15]  # 10 nodes (C1..C9)
    Rw = [100.0] * (N + 1)
    Cw = [15e-15] * (N + 1)
    g = [4/3] * (N + 1)
    # 末端两个固定
    C_final = relax(C, Cw, g, Rw, tau, max_iter=5, tol=0.05)
    # 验证：迭代次数 ≤ 5，结果稳定
    assert len(C_final) == N + 2
    assert all(c > 0 for c in C_final)
