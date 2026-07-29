import json
from pathlib import Path
from ule_opt.core.models import OptimReport, DeviceAdjust
from ule_opt.io.report import write_report


def test_write_report_creates_md_and_json(tmp_path):
    rep = OptimReport(
        case="table1",
        delay_original=61.4,
        delay_optimized=58.2,
        delay_reduction_pct=5.2,
        nodes=[DeviceAdjust(node="n1", c_orig=1.0, c_new=7.2, nfin=12, vt_recommend="LVT")],
        extra={"scenario": "scenario1"},
    )
    out = write_report(rep, out_dir=tmp_path)
    assert out["md"].exists()
    assert out["json"].exists()
    data = json.loads(out["json"].read_text(encoding="utf-8"))
    assert data["case"] == "table1"
    assert "Delay" in out["md"].read_text(encoding="utf-8")
