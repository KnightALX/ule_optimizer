from ule_opt.core.models import RCNode, RCValue, PathModel, OptimReport

def test_rc_node_basic():
    n = RCNode(name="n1", r=100.0, c=1e-15)
    assert n.r == 100.0
    assert n.gate_type == "INV"

def test_rc_node_negative_r_rejected():
    import pytest
    with pytest.raises(Exception):
        RCNode(name="n1", r=-1.0, c=1e-15)

def test_path_model_n_nodes():
    nodes = [RCNode(name=f"n{i}", r=100.0, c=1e-15) for i in range(4)]
    m = PathModel(nodes=nodes, tau=6.5e-15, R0=8800.0, C0=0.74e-15, source="CDL")
    assert m.N == 3  # 4 nodes = 3 segments

def test_optim_report_round_trip():
    r = OptimReport(case="table1", delay_original=42.0, delay_optimized=38.0,
                    delay_reduction_pct=9.5, nodes=[])
    d = r.model_dump()
    assert d["case"] == "table1"
