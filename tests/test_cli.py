from click.testing import CliRunner
from ule_opt.cli import main


def test_cli_help():
    r = CliRunner().invoke(main, ["--help"])
    assert r.exit_code == 0
    assert "run" in r.output
    assert "verify" in r.output
