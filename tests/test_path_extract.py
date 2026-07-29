from ule_opt.parsers.path_extract import extract_path, PathNotFound


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