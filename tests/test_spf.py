import gzip
from pathlib import Path
from ule_opt.parsers.spf import parse_spef, SpefDoc


def test_parse_minimal_spef():
    src = """*SPEF "IEEE 1481"
*NAME_MAP
*1 vdd
*2 gnd
*D_NET *1 0.0
*CONN
*1 *1 I
*CAP
*1 *1 0.001
*END
"""
    p = Path("tests/_tmp.spef")
    p.write_text(src)
    try:
        doc = parse_spef(p)
    finally:
        p.unlink()
    assert isinstance(doc, SpefDoc)
    assert doc.name_map["1"] == "vdd"


def test_parse_gz_spef(tmp_path):
    src = """*SPEF "IEEE 1481"
*NAME_MAP
*1 vdd
*END
"""
    p = tmp_path / "x.spef.gz"
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write(src)
    doc = parse_spef(p)
    assert doc.name_map["1"] == "vdd"
