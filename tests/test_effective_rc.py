from ule_opt.core.effective_rc import EffectiveRCLookup, DEFAULT_TABLE


def test_default_inv_lookup():
    lk = EffectiveRCLookup(DEFAULT_TABLE)
    ceff, reff = lk.lookup("INV")
    assert ceff > 0 and reff > 0


def test_unknown_gate_uses_custom():
    lk = EffectiveRCLookup(DEFAULT_TABLE)
    ceff, reff = lk.lookup("CUSTOM")
    # 缺省 fallback 应是 (1, 1)
    assert ceff == 1.0 and reff == 1.0


def test_override():
    lk = EffectiveRCLookup(DEFAULT_TABLE, overrides={"INV": (0.5, 0.5)})
    ceff, reff = lk.lookup("INV")
    assert math.isclose(ceff, 0.5)


import math  # for isclose above
