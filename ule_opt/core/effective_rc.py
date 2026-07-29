"""有效 R/C 查表（YAML 驱动 + 內建默认）。"""
from __future__ import annotations
from typing import Optional
import yaml


DEFAULT_TABLE: dict[str, dict[str, float]] = {
    "INV":    {"ceff_fF": 0.74, "reff_kOhm": 8.8},
    "NAND2":  {"ceff_fF": 1.0,  "reff_kOhm": 11.7},
    "NAND3":  {"ceff_fF": 1.3,  "reff_kOhm": 14.0},
    "NOR2":   {"ceff_fF": 1.1,  "reff_kOhm": 12.0},
    "NOR3":   {"ceff_fF": 1.4,  "reff_kOhm": 14.5},
    "BUF":    {"ceff_fF": 0.9,  "reff_kOhm": 9.0},
    "CUSTOM": {"ceff_fF": 0.74, "reff_kOhm": 8.8},
}


class EffectiveRCLookup:
    def __init__(
        self,
        base: dict[str, dict[str, float]] | None = None,
        overrides: Optional[dict[str, tuple[float, float]]] = None,
    ):
        self.table: dict[str, dict[str, float]] = base or DEFAULT_TABLE
        self.overrides = overrides or {}

    def lookup(self, gate_type: str) -> tuple[float, float]:
        """返回 (Ceff in F, Reff in Ω)。"""
        if gate_type in self.overrides:
            ceff_fF, reff_kOhm = self.overrides[gate_type]
            return ceff_fF, reff_kOhm
        if gate_type == "CUSTOM":
            return 1.0, 1.0
        row = self.table.get(gate_type) or self.table.get("CUSTOM")
        return row["ceff_fF"] * 1e-15, row["reff_kOhm"] * 1e3

    @classmethod
    def from_yaml(cls, path: str, overrides: Optional[dict] = None) -> "EffectiveRCLookup":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        merged = {**DEFAULT_TABLE, **data}
        return cls(merged, overrides)
