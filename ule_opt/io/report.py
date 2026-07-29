"""报告生成：控制台表格 + Markdown + JSON。"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

from ule_opt.core.models import OptimReport


def _md(report: OptimReport) -> str:
    lines = [
        f"# ULE 路径寻优报告 (Delay report) — {report.case}",
        "",
        f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}",
        f"- 原始总延时: {report.delay_original:.4f}",
        f"- 优化后总延时: {report.delay_optimized:.4f}",
        f"- 延时减少: {report.delay_reduction_pct:.2f}%",
        "",
        "## 节点级调整",
        "",
        "| Node | C_orig (fF) | C_new (fF) | nfin | VT | Note |",
        "|------|-------------|------------|------|-----|------|",
    ]
    for a in report.nodes:
        lines.append(
            f"| {a.node} | {a.c_orig*1e15:.3f} | {a.c_new*1e15:.3f} | {a.nfin} | {a.vt_recommend or '-'} | {a.note} |"
        )
    if report.extra:
        lines += ["", "## 附加信息", "", "```json", json.dumps(report.extra, indent=2, ensure_ascii=False), "```"]
    return "\n".join(lines) + "\n"


def write_report(report: OptimReport, out_dir: Optional[Path] = None) -> dict[str, Path]:
    """输出 Markdown + JSON + 控制台表格。返回文件路径。"""
    if out_dir is None:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = Path("reports") / f"{ts}-{report.case}"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{report.case}.md"
    json_path = out_dir / f"{report.case}.json"
    md_path.write_text(_md(report), encoding="utf-8")
    json_path.write_text(
        json.dumps(report.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    # 控制台
    console = Console()
    t = Table(title=f"ULE 寻优 — {report.case}", show_header=True, header_style="bold")
    t.add_column("Metric", style="cyan")
    t.add_column("Value", style="magenta")
    t.add_row("Delay original", f"{report.delay_original:.4f}")
    t.add_row("Delay optimized", f"{report.delay_optimized:.4f}")
    t.add_row("Reduction", f"{report.delay_reduction_pct:.2f}%")
    t.add_row("Nodes adjusted", str(len(report.nodes)))
    console.print(t)
    return {"md": md_path, "json": json_path, "dir": out_dir}
