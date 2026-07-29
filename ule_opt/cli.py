"""ule_opt CLI 入口。"""
from __future__ import annotations
import sys
import click
from pathlib import Path

from ule_opt.core.models import OptimReport, DeviceAdjust
from ule_opt.core.optimizer import scenario1, scenario2
from ule_opt.core.logical_effort import delay_path
from ule_opt.io.yaml_config import load_config, ConfigError
from ule_opt.io.report import write_report


@click.group()
@click.version_option()
def main():
    """ULE 路径寻优 CLI 工具。"""


@main.command()
@click.option("--config", "-c", required=True, help="YAML 配置文件路径")
def run(config: str):
    """运行寻优。"""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        click.echo(f"[ERR] {e}", err=True)
        sys.exit(2)

    # 简化：从 path_nodes 构造 PathModel
    from ule_opt.parsers.path_extract import extract_path, extract_path_from_cdl, PathNotFound
    if cfg.path_nodes:
        # 显式 YAML 节点清单优先
        extracted = extract_path(
            cdl=None, spef=None, node_list=cfg.path_nodes,
            R0=cfg.R0, C0=cfg.C0_fF * 1e-15,
        )
    else:
        # 自动 BFS 推断
        from ule_opt.parsers.cdl import parse_cdl as _parse_cdl
        from pathlib import Path as _Path
        cdl_path = _Path(cfg.cdl)
        if not cdl_path.exists():
            click.echo(f"[ERR] CDL 不存在: {cdl_path}", err=True)
            sys.exit(2)
        cdl_doc = _parse_cdl(cdl_path)
        try:
            extracted = extract_path_from_cdl(
                cdl_doc, cfg.source, cfg.target,
                R0=cfg.R0, C0=cfg.C0_fF * 1e-15,
            )
        except PathNotFound as e:
            click.echo(f"[ERR] 路径推断失败: {e}", err=True)
            sys.exit(2)
    nodes_c = [n.c_self for n in extracted.nodes]
    Rw = [n.r for n in extracted.nodes[:-1]]  # 段数 = N
    Cw = [n.c for n in extracted.nodes[:-1]]
    g = [n.g for n in extracted.nodes[:-1]]
    p = [n.p for n in extracted.nodes[:-1]]
    r_self = [n.r_self for n in extracted.nodes[:-1]]
    tau = cfg.R0 * cfg.C0_fF * 1e-15

    case = cfg.scenario
    if case == "scenario1":
        res = scenario1(nodes_c, Rw, Cw, g, p, r_self, tau, cfg.R0, cfg.C0_fF * 1e-15)
        adj = []
        for i, n in enumerate(extracted.nodes[1:-1], start=1):
            nfin = res.nfin_suggest[i - 1] if i - 1 < len(res.nfin_suggest) else 0
            vt = res.vt_recommend[i - 1] if i - 1 < len(res.vt_recommend) else "RVT"
            adj.append(DeviceAdjust(
                node=n.name, c_orig=nodes_c[i], c_new=res.C_new[i],
                nfin=nfin, vt_recommend=vt,
            ))
        rep = OptimReport(
            case=case,
            delay_original=res.delay_original,
            delay_optimized=res.delay_optimized,
            delay_reduction_pct=(res.delay_original - res.delay_optimized) / res.delay_original * 100,
            nodes=adj,
        )
    elif case == "scenario2":
        res = scenario2(nodes_c, Rw, Cw, g, p, r_self, tau, cfg.R0, cfg.C0_fF * 1e-15)
        s_in, s_out, d = res.best
        rep = OptimReport(
            case=case,
            delay_original=res.delay_original,
            delay_optimized=res.delay_optimized,
            delay_reduction_pct=(res.delay_original - res.delay_optimized) / res.delay_original * 100,
            nodes=[],
            extra={"best_s_in": s_in, "best_s_out": s_out, "ladder": [list(x) for x in res.ladder]},
        )
    else:
        click.echo(f"[ERR] 未知 scenario: {case}", err=True)
        sys.exit(2)

    write_report(rep)


@main.command()
@click.option("--case", "case", required=True, type=click.Choice(["table1", "scenario1", "scenario2"]))
def verify(case: str):
    """运行验证用例。"""
    from ule_opt.logger import get_logger
    _logger = get_logger("ule_opt.cli")
    _logger.info("verify subcommand: case=%s", case)
    from ule_opt.verify.table1 import run as run_table1
    from ule_opt.verify.scenario1 import run as run_s1
    from ule_opt.verify.scenario2 import run as run_s2
    if case == "table1":
        ok = run_table1()
    elif case == "scenario1":
        ok = run_s1()
    else:
        ok = run_s2()
    sys.exit(0 if ok else 1)


@main.command()
@click.argument("output", type=click.Path())
def template(output: str):
    """生成 YAML 模板。"""
    p = Path(output)
    p.write_text(
        """cdl: samples/synthesized_nand_chain.cdl
spef: ""
source: A
target: out
path_nodes: [A, n1, n2, n3, n4, n5, n6, n7, n8, out]
R0: 8800.0
C0_fF: 0.74
Rw_per_mm: 100.0
Cw_per_mm_fF: 15.0
scenario: scenario1
c_finger_unit_fF: 0.5
vt_threshold: 0.20
""",
        encoding="utf-8",
    )
    click.echo(f"已生成: {p}")


if __name__ == "__main__":
    main()
