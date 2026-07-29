"""场景 1/2 调度。"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Sequence
from .logical_effort import delay_path, relax


SCALE_LADDER = (0.7, 0.85, 1.0, 1.15)


@dataclass
class Scenario1Result:
    C_new: list[float]
    R_new: list[float]
    delay_original: float
    delay_optimized: float
    nfin_suggest: list[int] = field(default_factory=list)
    vt_recommend: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Scenario2Result:
    ladder: list[tuple[float, float, float]]  # (s_in, s_out, d)
    best: tuple[float, float, float]
    C_used: list[float]
    delay_original: float
    delay_optimized: float


def _delay_with_boundary(
    C: Sequence[float], Rw: Sequence[float], Cw: Sequence[float],
    g: Sequence[float], p: Sequence[float], r_self: Sequence[float],
    tau: float, R0: float,
) -> float:
    return delay_path(C, Rw, Cw, g, p, tau, R0)


def scenario1(
    C: list[float], Rw: Sequence[float], Cw: Sequence[float],
    g: Sequence[float], p: Sequence[float], r_self: Sequence[float],
    tau: float, R0: float, C0: float,
    c_finger_unit: float = 0.5e-15,
    vt_threshold: float = 0.20,
    max_iter: int = 5,
) -> Scenario1Result:
    """场景 1：固定 C_1, C_{N+1}，对内部重分配（总 C 守恒）。"""
    N = len(C) - 1
    if N < 2:
        raise ValueError("至少 3 个节点")

    delay_original = _delay_with_boundary(C, Rw, Cw, g, p, r_self, tau, R0)

    # Step A: 松弛迭代
    C_star = relax(C, Cw, g, Rw, tau, max_iter=max_iter, tol=0.05)

    # Step B: 守恒归一化
    orig_total = sum(C[1:N])
    star_total = sum(C_star[1:N])
    if star_total > 0:
        alpha = orig_total / star_total
    else:
        alpha = 1.0
    C_new = list(C)
    for i in range(1, N):
        C_new[i] = C_star[i] * alpha

    # Step C: 同样对 R（Rw[i]）做守恒缩放
    R_new = list(Rw)
    r_orig_total = sum(Rw[1:N])
    # 用同样 alpha 近似保持总 R·C
    if r_orig_total > 0:
        r_star_total = sum(Rw[1:N])  # Rw 来自原值，relax 不动 Rw
        for i in range(1, N):
            R_new[i] = Rw[i] * alpha

    # Step D: 一次额外松弛迭代修复归一化破坏
    C_new = relax(C_new, Cw, g, R_new, tau, max_iter=2, tol=0.02)

    delay_optimized = _delay_with_boundary(C_new, R_new, Cw, g, p, r_self, tau, R0)

    # Step E: 器件映射
    nfin_suggest = []
    vt_recommend = []
    for i in range(1, N):
        # nfin = round((C_i/C0 - 1) / c_finger_unit)，钳到非负
        nfin = max(0, round((C_new[i] / C0 - 1.0) / c_finger_unit))
        nfin_suggest.append(nfin)
        delta = (C_new[i] - C[i]) / C[i] if C[i] > 0 else 0
        if delta > vt_threshold:
            vt_recommend.append("LVT")
        elif delta < -vt_threshold:
            vt_recommend.append("HVT")
        else:
            vt_recommend.append("RVT")

    return Scenario1Result(
        C_new=C_new, R_new=R_new,
        delay_original=delay_original, delay_optimized=delay_optimized,
        nfin_suggest=nfin_suggest, vt_recommend=vt_recommend,
        note="内部 R/C 守恒重分配",
    )


def scenario2(
    C: list[float], Rw: Sequence[float], Cw: Sequence[float],
    g: Sequence[float], p: Sequence[float], r_self: Sequence[float],
    tau: float, R0: float, C0: float,
    scale_ladder: Sequence[float] = SCALE_LADDER,
) -> Scenario2Result:
    """场景 2：固定内部 R/C，扫描边界 4×4 = 16 档。"""
    N = len(C) - 1
    if N < 2:
        raise ValueError("至少 3 个节点")

    delay_original = _delay_with_boundary(C, Rw, Cw, g, p, r_self, tau, R0)
    C1_orig = C[0]
    Cout_orig = C[-1]

    ladder: list[tuple[float, float, float]] = []
    best = (1.0, 1.0, delay_original)
    best_C = list(C)
    for s_in in scale_ladder:
        for s_out in scale_ladder:
            C_trial = list(C)
            C_trial[0] = C1_orig * s_in
            C_trial[-1] = Cout_orig * s_out
            d = _delay_with_boundary(C_trial, Rw, Cw, g, p, r_self, tau, R0)
            ladder.append((s_in, s_out, d))
            if d < best[2]:
                best = (s_in, s_out, d)
                best_C = C_trial

    return Scenario2Result(
        ladder=ladder, best=best, C_used=best_C,
        delay_original=delay_original, delay_optimized=best[2],
    )
