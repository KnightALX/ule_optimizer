from pathlib import Path
from ule_opt.parsers.cdl import parse_cdl, Subckt, Resistor, Capacitor


def test_parse_simple_subckt():
    src = """
* comment
.SUBCKT nand_chain A Z vdd gnd
R1 net1 net2 100
C1 net2 0 1e-15
.ENDS
"""
    p = Path("tests/_tmp_cdl.cki")
    p.write_text(src)
    try:
        r = parse_cdl(p)
    finally:
        p.unlink()
    assert any(isinstance(x, Subckt) and x.name == "nand_chain" for x in r.cells)
    assert any(isinstance(x, Resistor) and x.value == 100 for x in r.cells)
    assert any(isinstance(x, Capacitor) and x.value == 1e-15 for x in r.cells)
