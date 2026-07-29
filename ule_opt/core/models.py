"""数据模型。"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, computed_field


class RCValue(BaseModel):
    r: float = Field(ge=0, description="电阻 (Ω)")
    c: float = Field(ge=0, description="电容 (F)")


class RCNode(BaseModel):
    name: str
    r: float = Field(ge=0, description="段 i 互连电阻 (Ω)")
    c: float = Field(ge=0, description="段 i 互连总电容 (F)")
    gate_type: Literal["INV", "NAND2", "NAND3", "NOR2", "NOR3", "BUF", "CUSTOM"] = "INV"
    g: float = Field(default=1.0, ge=0, description="逻辑功 (论文式 3)")
    p: float = Field(default=1.0, ge=0, description="寄生功 (论文式 3)")
    ceff_override: Optional[float] = None
    reff_override: Optional[float] = None
    # 门自身电容/电阻（来自 CDL/SPEF）
    c_self: float = Field(default=0.0, ge=0, description="门 i 输入电容 (F)")
    r_self: float = Field(default=0.0, ge=0, description="门 i 输出电阻 (Ω)")
    c_parasitic: float = Field(default=0.0, ge=0, description="门 i 寄生输出电容 (F)")


class PathModel(BaseModel):
    nodes: list[RCNode]            # 含首末共 N+1 个
    tau: float                      # R0 * C0
    R0: float
    C0: float
    source: Literal["CDL", "SPF"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def N(self) -> int:
        return len(self.nodes) - 1


class DeviceAdjust(BaseModel):
    node: str
    c_orig: float
    c_new: float
    nfin: int
    vt_recommend: Optional[Literal["LVT", "RVT", "HVT"]] = None
    note: str = ""


class OptimReport(BaseModel):
    case: str
    delay_original: float
    delay_optimized: float
    delay_reduction_pct: float
    nodes: list[DeviceAdjust] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)
