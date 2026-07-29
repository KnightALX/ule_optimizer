import math
import pytest
from ule_opt.core.pi1 import to_pi1, transform_segment, Pi1Segment


def test_to_pi1_basic():
    r, c1, c2 = to_pi1(100.0, 2e-15)
    assert r == 100.0
    assert c1 == 1e-15
    assert c2 == 1e-15


def test_to_pi1_zero_cap():
    r, c1, c2 = to_pi1(50.0, 0.0)
    assert r == 50.0 and c1 == 0.0 and c2 == 0.0


def test_to_pi1_negative_rejected():
    with pytest.raises(ValueError):
        to_pi1(-1.0, 1e-15)


def test_transform_segment_returns_dataclass():
    seg = transform_segment(r_wire=200.0, c_wire=4e-15)
    assert isinstance(seg, Pi1Segment)
    assert math.isclose(seg.c1, 2e-15)
    assert math.isclose(seg.c2, 2e-15)