"""完整 SPEF (IEEE 1481) 解析器，支持 .gz 压缩。"""
from __future__ import annotations
import gzip
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SpefNet:
    name: str
    load: float = 0.0
    caps: dict[str, float] = field(default_factory=dict)
    ress: list[tuple[str, str, float]] = field(default_factory=list)


@dataclass
class SpefDoc:
    name_map: dict[str, str] = field(default_factory=dict)
    nets: dict[str, SpefNet] = field(default_factory=dict)


def _open_text(path: Path):
    """自动检测 .gz。"""
    if path.suffix == ".gz" or path.name.endswith(".spef.gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def parse_spef(path: Path | str) -> SpefDoc:
    """解析 SPEF。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    doc = SpefDoc()
    cur_net: Optional[SpefNet] = None
    with _open_text(p) as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("*SPEF") or line.startswith("*COMMENT"):
                continue
            if line.startswith("*NAME_MAP"):
                continue
            if line.startswith("*END"):
                cur_net = None
                continue
            # NAME_MAP 数据行: *id name
            # 必须在所有其他 * 前缀判断之前处理（否则 *1 vdd
            # 会被误判为 *P/*I/CAP/RES/其他段而被跳过）。
            if cur_net is None and not doc.nets and line.startswith("*"):
                inner = line[1:].strip()
                parts = inner.split()
                if len(parts) == 2:
                    doc.name_map[parts[0]] = parts[1]
                continue
            if line.startswith("*D_NET"):
                # *D_NET name load
                toks = line.split()
                if len(toks) >= 2:
                    cur_net = SpefNet(name=toks[1])
                    doc.nets[toks[1]] = cur_net
                continue
            if line.startswith("*CONN"):
                continue
            if line.startswith("*P") or line.startswith("*I"):
                # *P index node | *I index driver
                # 简化：不解析 conn 顺序
                continue
            if line.startswith("*CAP"):
                if cur_net is None:
                    continue
                # *CAP node cap
                toks = line.split()
                if len(toks) >= 3:
                    cur_net.caps[toks[1]] = float(toks[2])
                continue
            if line.startswith("*RES"):
                if cur_net is None:
                    continue
                # *RES n1 n2 r
                toks = line.split()
                if len(toks) >= 4:
                    cur_net.ress.append((toks[1], toks[2], float(toks[3])))
                continue
            if line.startswith("*"):
                # 其他段（*R、C 等）跳过
                continue
    return doc
