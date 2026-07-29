"""YAML 配置加载与 Pydantic 校验。"""
from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, field_validator


class ConfigError(Exception):
    pass


class _Config(BaseModel):
    cdl: str
    spef: str = ""
    source: str = Field(..., description="源节点 A")
    target: str = Field(..., description="目标节点 B")
    path_nodes: list[str] = Field(default_factory=list)
    R0: float = 8800.0
    C0_fF: float = 0.74
    Rw_per_mm: float = 100.0
    Cw_per_mm_fF: float = 15.0
    scenario: str = Field(default="scenario1")
    c_finger_unit_fF: float = 0.5
    vt_threshold: float = 0.20
    effective_rc_yaml: str = ""

    @field_validator("cdl")
    @classmethod
    def _cdl_exists(cls, v):
        # 不强制存在（允许纯 SPEF 场景）
        return v


def load_config(path: str | Path) -> _Config:
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"YAML 不存在: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    try:
        return _Config(**data)
    except Exception as e:
        raise ConfigError(f"YAML 校验失败: {e}") from e