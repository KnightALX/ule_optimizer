from ule_opt.core.effective_rc import EffectiveRCLookup, DEFAULT_TABLE


def test_default_inv_lookup():
    lk = EffectiveRCLookup(DEFAULT_TABLE)
    ceff, reff = lk.lookup("INV")
    assert ceff > 0 and reff > 0


def test_unknown_gate_uses_custom():
    lk = EffectiveRCLookup(DEFAULT_TABLE)
    ceff, reff = lk.lookup("UNKNOWN_GATE_X")
    # 未知门型 fallback 到 CUSTOM 默认行（fF/kΩ → F/Ω）
    assert math.isclose(ceff, 0.74e-15)
    assert math.isclose(reff, 8.8e3)


def test_override():
    # overrides 单位为 fF / kΩ：0.5 fF → 0.5e-15 F
    lk = EffectiveRCLookup(DEFAULT_TABLE, overrides={"INV": (0.5, 0.5)})
    ceff, reff = lk.lookup("INV")
    assert math.isclose(ceff, 0.5e-15)
    assert math.isclose(reff, 0.5e3)


import math  # for isclose above
