"""π-1 (PI-1) 模型：单段 RC 折算为 (R, C/2, C/2)。

用户提示中的 PAI-1 解释为 π-1（单段 RC π 集总），与论文 [ULE] L42
默认的 π 模型一致。
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Pi1Segment:
    """单段 π 集总模型。"""
    r: float          # 段总电阻 (Ω)
    c1: float         # 左端电容 (F)
    c2: float         # 右端电容 (F)


def to_pi1(r_wire: float, c_wire: float) -> tuple[float, float, float]:
    """π-1 折算：(R, C/2, C/2)。

    Args:
        r_wire: 段总电阻 (Ω)
        c_wire: 段总电容 (F)

    Returns:
        (r, c1, c2)

    Raises:
        ValueError: 任一参数为负。
    """
    if r_wire < 0 or c_wire < 0:
        raise ValueError(f"π-1 输入非负: r={r_wire}, c={c_wire}")
    return r_wire, 0.5 * c_wire, 0.5 * c_wire


def transform_segment(r_wire: float, c_wire: float) -> Pi1Segment:
    """便捷接口：返回 Pi1Segment。"""
    r, c1, c2 = to_pi1(r_wire, c_wire)
    return Pi1Segment(r=r, c1=c1, c2=c2)