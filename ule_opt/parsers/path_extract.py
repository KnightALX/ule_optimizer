"""路径抽取。

策略（按用户决策）：
- 优先使用 YAML 显式节点清单
- 次之：用调用图拓扑序 + 名字模式推断
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ule_opt.logger import get_logger

_logger = get_logger("ule_opt.parsers.path_extract")


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


# ---------------------------------------------------------------------------
# BFS 调用图路径推断（CDL XInstance 调用图）
# ---------------------------------------------------------------------------

def _build_cdl_graph(cdl) -> tuple[set[str], dict[str, list[str]]]:
    """从 CDL doc.cells 构造 net 邻接表。

    启发式：XInstance.nets 的最后一个 net 视作输出，其它 net 视作输入。
    未知 subckt（未在 doc.subckts 中出现）→ 跳过该 X 边，不抛错。
    """
    from ule_opt.parsers.cdl import XInstance

    known_subckts: set[str] = set(cdl.subckts.keys())
    nets: set[str] = set()
    adj: dict[str, list[str]] = {}

    for cell in cdl.cells:
        if not isinstance(cell, XInstance):
            continue
        if cell.model not in known_subckts:
            # 未知 subckt：跳过该边，不抛错
            continue
        nets_list = cell.nets
        if len(nets_list) < 2:
            continue
        out_net = nets_list[-1]
        in_nets = nets_list[:-1]
        nets.add(out_net)
        for n in in_nets:
            nets.add(n)
        for n in in_nets:
            if n == out_net:
                continue
            adj.setdefault(n, []).append(out_net)
            adj.setdefault(out_net, [])  # 保证输出节点也存在 key

    x_edge_count = sum(len(v) for v in adj.values())
    _logger.info("build_graph: %d nets, %d X-edges", len(nets), x_edge_count)

    # 兜底：出现但无出边的孤立 net 也加入 nets（便于"存在性"判定）
    return nets, adj


def extract_path_from_cdl(
    cdl,
    source: str,
    target: str,
    R0: float = 8800.0,
    C0: float = 0.74e-15,
) -> ExtractedPath:
    """从 CDL 调用图做 BFS 路径推断。

    图模型：
        顶点 = net（CDL 节点名）
        有向边 = XInstance 输入端口 → 输出端口
        启发式：XInstance.nets 最后一个 net 视作输出，其余视作输入。

    Returns:
        ExtractedPath: nodes 按 BFS 顺序（source → … → target），长度 ≥ 2。

    Raises:
        PathNotFound: source 不存在 / target 不存在 / source==target / 不可达。
    """
    from ule_opt.core.models import RCNode

    if source == target:
        raise PathNotFound(f"source 等于 target: {source}")

    nets, adj = _build_cdl_graph(cdl)

    if source not in nets:
        raise PathNotFound(f"source 不存在: {source}")
    if target not in nets:
        raise PathNotFound(f"target 不存在: {target}")

    # BFS（最短路径）
    visited: set[str] = {source}
    parent: dict[str, Optional[str]] = {source: None}
    from collections import deque
    q: deque[str] = deque([source])
    _logger.info("BFS start: source=%s, target=%s", source, target)
    levels = 0
    target_reached = False
    while q:
        cur = q.popleft()
        if cur == target:
            _logger.info(
                "BFS step: cur=%s, target reached, break",
                cur,
            )
            target_reached = True
            break
        for nxt in adj.get(cur, ()):
            if nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = cur
            _logger.info(
                "BFS step: cur=%s -> nxt=%s (parent[%s]=%s)",
                cur, nxt, nxt, cur,
            )
            q.append(nxt)
        levels += 1
        _logger.info(
            "BFS step: cur=%s, visited=%d, queue=[%s]",
            cur, len(visited), ", ".join(q),
        )

    if target not in parent:
        raise PathNotFound(f"不可达: {source} → {target}")

    _logger.info(
        "BFS done: %d levels traversed, %d nodes visited",
        levels, len(visited),
    )

    # 重建路径（按 BFS 顺序）
    seq: list[str] = []
    cur: Optional[str] = target
    while cur is not None:
        _logger.info(
            "path rebuild: %s, parent=%s%s",
            cur, parent[cur],
            " (root)" if parent[cur] is None else "",
        )
        seq.append(cur)
        cur = parent[cur]
    seq.reverse()

    # 占位 RCNode（不解析 X subckt 类型）
    L = len(seq)
    nodes = []
    for i, name in enumerate(seq):
        # 首/末节点 r_self=R0（驱动/负载），中间节点 r_self=R0*4/3（INV 典型逻辑功）
        if i in (0, L - 1):
            r_self = R0
        else:
            r_self = R0 * 4 / 3
        n = RCNode(
            name=name,
            r=100.0, c=15e-15,
            gate_type="INV", g=4 / 3, p=1.0,
            c_self=C0, r_self=r_self,
        )
        nodes.append(n)

    _logger.info(
        "final path: %s (%d nodes, %d edges)",
        " -> ".join(seq), len(seq), len(seq) - 1,
    )

    return ExtractedPath(nodes=nodes)