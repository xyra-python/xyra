import pytest
from xyra.datastructures import Headers

def test_headers_init_validation():
    with pytest.raises(ValueError):
        h = Headers({"a": "b\n"})

def test_headers_update_validation():
    h = Headers()
    with pytest.raises(ValueError):
        h.update({"a": "b\n"})

def test_headers_extend_validation():
    h = Headers()
    with pytest.raises(ValueError):
        h.extend({"a": "b\n"})

def test_headers_multiple_keys():
    h = Headers()
    h.extend([("a", "1"), ("a", "2")])
    assert len(h.getall("a")) == 2

    h2 = Headers([("a", "1"), ("a", "2")])
    assert len(h2.getall("a")) == 2
