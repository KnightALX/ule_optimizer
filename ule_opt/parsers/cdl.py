"""CDL / Spectre / HSPICE 子集解析。

支持的实例：
- .SUBCKT name ports ...   / .ENDS
- Rxxx n1 n2 value         (电阻)
- Cxxx n1 n2 value         (电容)
- Xxxx n1 n2 ... subname   (子电路调用，可选)
- Mxxx ... (晶体管，跳过)
- .GLOBAL vdd gnd          (全局节点)
- * 注释
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union


@dataclass
class Resistor:
    name: str
    n1: str
    n2: str
    value: float


@dataclass
class Capacitor:
    name: str
    n1: str
    n2: str
    value: float


@dataclass
class XInstance:
    name: str
    nets: list[str]
    model: str


@dataclass
class Subckt:
    name: str
    ports: list[str]
    content_lines: list[str] = field(default_factory=list)


@dataclass
class CdlDocument:
    globals: list[str] = field(default_factory=list)
    subckts: dict[str, Subckt] = field(default_factory=dict)
    cells: list[Union[Subckt, Resistor, Capacitor, XInstance]] = field(default_factory=list)


def _strip_comment(line: str) -> str:
    i = line.find("*")
    return line[:i] if i >= 0 else line


def parse_cdl(path: Path | str) -> CdlDocument:
    """解析 CDL 文件。

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: SUBCKT 未闭合
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    doc = CdlDocument()
    stack: list[Subckt] = []
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = _strip_comment(raw).strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith(".GLOBAL"):
                doc.globals = line.split()[1:]
                continue
            if upper.startswith(".SUBCKT"):
                parts = line.split()
                # .SUBCKT name p1 p2 ...
                name = parts[1]
                ports = parts[2:]
                sk = Subckt(name=name, ports=ports)
                doc.subckts[name] = sk
                if not stack:
                    doc.cells.append(sk)
                stack.append(sk)
                continue
            if upper.startswith(".ENDS"):
                if not stack:
                    raise ValueError(f"未匹配的 .ENDS at line: {raw.rstrip()}")
                stack.pop()
                continue
            # R/C/X 顶层实例 + subckt 内部都收集到 doc.cells
            first = line[0]
            if first.upper() == "R":
                toks = line.split()
                if len(toks) >= 4:
                    doc.cells.append(Resistor(toks[0], toks[1], toks[2], float(toks[3])))
            elif first.upper() == "C":
                toks = line.split()
                if len(toks) >= 4:
                    doc.cells.append(Capacitor(toks[0], toks[1], toks[2], float(toks[3])))
            elif first.upper() == "X":
                toks = line.split()
                if len(toks) >= 2:
                    doc.cells.append(XInstance(toks[0], toks[1:-1], toks[-1]))
            # M/其他器件：跳过（不在本工具域）
            if stack:
                # 在 subckt 内部：暂存文本
                stack[-1].content_lines.append(line)
    if stack:
        raise ValueError(f"未闭合的 .SUBCKT: {[s.name for s in stack]}")
    return doc
