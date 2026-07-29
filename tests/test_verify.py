from ule_opt.verify.table1 import run as run_table1
from ule_opt.verify.scenario1 import run as run_s1
from ule_opt.verify.scenario2 import run as run_s2


def test_table1_verify():
    assert run_table1() is True


def test_scenario1_verify():
    assert run_s1() is True


def test_scenario2_verify():
    assert run_s2() is True