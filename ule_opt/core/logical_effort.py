"""论文 [ULE] 公式 (1)–(20) 与松弛迭代。

实现范围：
- `delay_segment` ：论文式 (4) 单段 ULE 延迟
- `delay_path`    ：论文式 (7) N 段路径总延迟
- `compute_xopt`  ：论文式 (19)/(20) 最优尺寸因子
- `relax`         ：论文式 (16) 松弛迭代 (a/b/c 三步) [ULE] L181–L189
"""
from __future__ import annotations
import math
from typing import Sequence


def delay_segment(
    R_i: float, C_i: float, C_pi: float,
    R_wi: float, C_wi: float, C_next: float,
    g_i: float, p_i: float, tau: float,
) -> float:
    """论文式 (4): ULE 单段延迟。

    公式：
        d_i = g_i * (h_i + h_wi) + (p_i + p_wi)
        h_i  = C_next / C_i
        h_wi = C_wi / C_i
        p_wi = R_wi * (0.5 * C_wi + C_next) / tau

    Args:
        R_i: 段 i 门输出电阻 (Ω)（论文式 2）。
        C_i: 段 i 门输入电容 (F)。
        C_pi: 段 i 门寄生输出电容 (F)（当前实现未直接使用，预留）。
        R_wi: 段 i 互连电阻 (Ω)。
        C_wi: 段 i 互连总电容 (F)。
        C_next: 段 i+1 的输入电容 (F)，即 C_{i+1}。
        g_i: 段 i 逻辑功（论文式 3）。
        p_i: 段 i 寄生功（论文式 3）。
        tau: 特征时间常数 R0 * C0 (s)。

    Returns:
        单段归一化延迟 d_i (无量纲, τ 单位)。

    Raises:
        ValueError: C_i 或 tau 非正。
    """
    if C_i <= 0:
        raise ValueError(f"C_i 必须 > 0, got {C_i}")
    if tau <= 0:
        raise ValueError(f"tau 必须 > 0, got {tau}")
    h_i = C_next / C_i
    h_wi = C_wi / C_i
    p_wi = R_wi * (0.5 * C_wi + C_next) / tau
    return g_i * (h_i + h_wi) + (p_i + p_wi)


def delay_path(
    nodes_c: Sequence[float],
    r_w: Sequence[float],
    c_w: Sequence[float],
    g: Sequence[float],
    p: Sequence[float],
    tau: float,
    R0: float,
) -> float:
    """N 段路径总延迟 (论文式 7)。

    d = Σ_{i=1..N} d_i

    段数 N = len(nodes_c) - 1 (含 C_1..C_{N+1} 共 N+1 个节点)。

    Args:
        nodes_c: 节点输入电容序列 (F)，长度 N+1。
        r_w: 段互连电阻序列 (Ω)，长度 N。
        c_w: 段互连总电容序列 (F)，长度 N。
        g: 段逻辑功序列，长度 N。
        p: 段寄生功序列，长度 N。
        tau: 特征时间常数 (s)。
        R0: 参考反相器输出电阻 (Ω)，用于 R_i = R0 * g_i 的基础 LE 假设。

    Returns:
        归一化路径总延迟 (无量纲, τ 单位)。

    Raises:
        ValueError: 节点数 < 2 或段序列长度不匹配。
    """
    N = len(nodes_c) - 1
    if N < 1:
        raise ValueError("至少 2 个节点")
    if not (len(r_w) == N and len(c_w) == N and len(g) == N and len(p) == N):
        raise ValueError("段序列长度必须匹配 N")
    total = 0.0
    for i in range(N):
        # 简化模型：R_i = R0 * g_i, C_pi = 0（基础 LE 假设）
        R_i = R0 * g[i]
        C_pi = 0.0
        total += delay_segment(
            R_i=R_i, C_i=nodes_c[i], C_pi=C_pi,
            R_wi=r_w[i], C_wi=c_w[i], C_next=nodes_c[i + 1],
            g_i=g[i], p_i=p[i], tau=tau,
        )
    return total


def compute_xopt(R0: float, C0: float, Cw: float, Rw: float, g: float) -> float:
    """论文式 (19): x_opt = sqrt(R0*Cw/(Rw*C0) * g)，g=1 退化为式 (20)。

    Args:
        R0: 参考反相器输出电阻 (Ω)。
        C0: 参考反相器输入电容 (F)。
        Cw: 互连总电容 (F)。
        Rw: 互连总电阻 (Ω)。
        g: 段的逻辑功。

    Returns:
        最优尺寸因子 x_opt (无量纲)。

    Raises:
        ValueError: 任一参数非法 (≤0 或 Cw<0)。
    """
    if R0 <= 0 or C0 <= 0 or Cw < 0 or Rw <= 0 or g <= 0:
        raise ValueError(f"非法 xopt 参数: R0={R0} C0={C0} Cw={Cw} Rw={Rw} g={g}")
    return math.sqrt(R0 * Cw / (Rw * C0) * g)


def relax(
    C: list[float],
    Cw: Sequence[float],
    g: Sequence[float],
    Rw: Sequence[float],
    tau: float,
    max_iter: int = 5,
    tol: float = 0.05,
) -> list[float]:
    """论文式 (16) 松弛迭代 [ULE] L181–L189。

    对内部节点 C_2..C_N 反复执行论文式 (16) 的 a/b/c 三步更新，
    直到最大相对变化 < tol 或达到 max_iter。
    边界节点 C_1, C_{N+1} 保持固定。

    更新公式（内部 i ∈ [1, N)）：
        le   = sqrt(C_{i-1} * C_{i+1})
        wc   = sqrt(1 + Cw_i / C_{i+1})
        rterm = Rw_{i-1} * C_{i-1} / tau
        gterm = g_i / (g_{i-1} + rterm)
        C_i_new = le * wc * sqrt(gterm)

    Args:
        C: 节点电容初始值 (F)，长度 N+1 (含首末)。
        Cw: 段 i 互连总电容 (F)，长度 N (与 C 一一对应 C_1..C_N)。
        g: 段 i 逻辑功，长度 N。
        Rw: 段 i 互连电阻 (Ω)，长度 N。
        tau: 特征时间常数 (s)。
        max_iter: 最大迭代次数。
        tol: 收敛阈值 (相对变化)。

    Returns:
        迭代后的节点电容列表 (F)，长度 N+1。

    Raises:
        ValueError: C 长度 < 3。
    """
    if len(C) < 3:
        raise ValueError("C 至少 3 个元素")
    N = len(C) - 1
    C_cur = list(C)
    for _ in range(max_iter):
        C_new = list(C_cur)
        for i in range(1, N):
            le = math.sqrt(C_cur[i - 1] * C_cur[i + 1])
            wc = math.sqrt(1.0 + Cw[i] / C_cur[i + 1])
            r_term = Rw[i - 1] * C_cur[i - 1] / tau
            g_term = g[i] / (g[i - 1] + r_term)
            if g_term < 0:
                g_term = 0
            C_new[i] = le * wc * math.sqrt(g_term)
        # 相对变化
        max_rel = max(
            abs(C_new[i] - C_cur[i]) / C_cur[i] for i in range(1, N) if C_cur[i] > 0
        )
        C_cur = C_new
        if max_rel < tol:
            break
    return C_cur
