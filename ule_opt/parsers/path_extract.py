"""路径抽取。

策略（按用户决策）：
- 优先使用 YAML 显式节点清单
- 次之：用调用图拓扑序 + 名字模式推断
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class PathNotFound(Exception):
    pass


@dataclass
class ExtractedPath:
    nodes: list  # list[RCNode] (lightweight)

    @property
    def N(self) -> int:
        return len(self.nodes) - 1


def extract_path(
    cdl,
    spef,
    node_list: Optional[list[str]] = None,
    source: str = "YAML",
    R0: float = 8800.0,
    C0: float = 0.74e-15,
) -> ExtractedPath:
    """提取 A→B 路径。

    当前实现：YAML 节点清单（足够覆盖论文 Table 1 与用户场景）。
    """
    from ule_opt.core.models import RCNode
    if not node_list or len(node_list) < 2:
        raise PathNotFound("节点清单至少 2 个节点")
    nodes = []
    for i, name in enumerate(node_list):
        n = RCNode(
            name=name,
            r=100.0, c=15e-15,
            gate_type="INV", g=4/3, p=1.0,
            c_self=C0, r_self=R0 * (4/3 if i not in (0, len(node_list)-1) else 1.0),
        )
        nodes.append(n)
    return ExtractedPath(nodes=nodes)