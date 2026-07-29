from ule_opt.parsers.path_extract import extract_path, extract_path_from_cdl, PathNotFound


def test_extract_by_node_list():
    r = extract_path(
        cdl=None,  # 走显式节点清单
        spef=None,
        node_list=["in", "n1", "n2", "n3", "out"],
    )
    assert r.N == 4
    assert r.nodes[0].name == "in"
    assert r.nodes[-1].name == "out"


def test_extract_unknown_raises():
    import pytest
    with pytest.raises(PathNotFound):
        extract_path(cdl=None, spef=None, node_list=["only_one"])


# ---------------------------------------------------------------------------
# BFS 路径推断（extract_path_from_cdl）
# ---------------------------------------------------------------------------

from ule_opt.parsers.cdl import parse_cdl, XInstance, Subckt, CdlDocument
import pytest


def _make_chain_cdl(n: int = 3) -> CdlDocument:
    """构造含 n 个 X 实例串联的 CDL：in -> n1 -> n2 -> ... -> out。

    启发式：XInstance.nets 最后一个 net 是输出，其余是输入。
    """
    doc = CdlDocument()
    doc.subckts["INV"] = Subckt(name="INV", ports=["in", "out"])
    nets_chain = ["in"] + [f"n{i+1}" for i in range(n - 1)] + ["out"]
    for i in range(n):
        xi = XInstance(name=f"X{i}", nets=[nets_chain[i], nets_chain[i + 1]], model="INV")
        doc.cells.append(xi)
    return doc


def test_bfs_simple_path():
    """3 X 实例串联：in -> n1 -> n2 -> out，共 4 节点。"""
    doc = _make_chain_cdl(n=3)
    r = extract_path_from_cdl(cdl=doc, source="in", target="out")
    assert r.N == 3  # 段数 = N = 节点数 - 1
    assert [n.name for n in r.nodes] == ["in", "n1", "n2", "out"]


def test_bfs_branching():
    """菱形图：A -> B -> D, A -> C -> D；BFS 选最短（2 跳 vs 4 跳）。"""
    doc = CdlDocument()
    doc.subckts["INV"] = Subckt(name="INV", ports=["in", "out"])
    # 两条路径：A->B->D (2 跳), A->C->D (经由 X2->X3->X4 共 4 跳)
    edges = [
        ("X0", ["A", "B"], "INV"),       # A -> B
        ("X1", ["B", "D"], "INV"),       # B -> D (最短路径)
        ("X2", ["A", "C"], "INV"),       # A -> C
        ("X3", ["C", "M"], "INV"),       # C -> M
        ("X4", ["M", "D"], "INV"),       # M -> D
    ]
    for name, nets, model in edges:
        doc.cells.append(XInstance(name=name, nets=nets, model=model))
    r = extract_path_from_cdl(cdl=doc, source="A", target="D")
    assert [n.name for n in r.nodes] == ["A", "B", "D"]
    assert r.N == 2


def test_bfs_unreachable():
    """source/target 不连通。"""
    doc = CdlDocument()
    doc.subckts["INV"] = Subckt(name="INV", ports=["in", "out"])
    doc.cells.append(XInstance(name="X0", nets=["A", "B"], model="INV"))
    doc.cells.append(XInstance(name="X1", nets=["C", "D"], model="INV"))
    with pytest.raises(PathNotFound) as exc:
        extract_path_from_cdl(cdl=doc, source="A", target="D")
    assert "不可达" in str(exc.value)


def test_bfs_source_equals_target():
    with pytest.raises(PathNotFound) as exc:
        extract_path_from_cdl(cdl=_make_chain_cdl(3), source="in", target="in")
    assert "等于 target" in str(exc.value)


def test_bfs_unknown_source():
    doc = _make_chain_cdl(3)
    with pytest.raises(PathNotFound) as exc:
        extract_path_from_cdl(cdl=doc, source="NOPE", target="out")
    assert "source 不存在" in str(exc.value)


def test_bfs_self_loop():
    """自环 X：A -> A 加上 A -> B；BFS 应能正确处理（不会死循环），且能找到 A -> B。"""
    doc = CdlDocument()
    doc.subckts["INV"] = Subckt(name="INV", ports=["in", "out"])
    # 自环：A -> A（启发式下 nets=[A, A]，仅产生 out_net=A；in_nets 也含 A；filter 后无自边）
    doc.cells.append(XInstance(name="XS", nets=["A", "A"], model="INV"))
    # 正常边：A -> B
    doc.cells.append(XInstance(name="X1", nets=["A", "B"], model="INV"))
    # B -> C
    doc.cells.append(XInstance(name="X2", nets=["B", "C"], model="INV"))
    r = extract_path_from_cdl(cdl=doc, source="A", target="C")
    assert [n.name for n in r.nodes] == ["A", "B", "C"]
    assert r.N == 2