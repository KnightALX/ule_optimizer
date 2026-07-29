import math
from pathlib import Path
from ule_opt.io.yaml_config import load_config, ConfigError


def test_load_nand_chain():
    cfg = load_config("samples/configs/nand_chain.yaml")
    assert cfg.cdl.endswith(".cdl")
    assert cfg.spef.endswith(".spef") or cfg.spef.endswith(".spef.gz")
    assert cfg.source == "A"
    assert cfg.target == "out"
    assert len(cfg.path_nodes) >= 2


def test_load_missing_raises(tmp_path):
    p = tmp_path / "no.yaml"
    try:
        load_config(str(p))
    except ConfigError:
        pass
    else:
        assert False, "expected ConfigError"