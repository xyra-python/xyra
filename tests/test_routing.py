import importlib
import sys
from unittest.mock import patch

import xyra.routing
from xyra.routing import Router


def test_parse_path_fallback_when_cffi_missing():
    try:
        with patch.dict(sys.modules, {"xyra._libxyra": None}):
            if "xyra.routing" in sys.modules:
                del sys.modules["xyra.routing"]
            fallback_routing = importlib.import_module("xyra.routing")
            path, params = fallback_routing.parse_path("/users/{id}")
            assert path == "/users/{id}"
            assert params == []
    finally:
        if "xyra.routing" in sys.modules:
            del sys.modules["xyra.routing"]
        sys.modules["xyra.routing"] = xyra.routing
        importlib.reload(xyra.routing)


def test_router_creation():
    router = Router()
    assert router is not None


def test_router_add_route():
    router = Router()
    router.add_route("GET", "/", lambda: "test")
    assert len(router.routes) == 1


def test_router_is_async_cached():
    router = Router()

    def sync_handler(req, res):
        return "sync"

    async def async_handler(req, res):
        return "async"

    router.add_route("GET", "/sync", sync_handler)
    router.add_route("GET", "/async", async_handler)

    assert router.routes[0]["is_async"] is False
    assert router.routes[1]["is_async"] is True


def test_router_api_stability():
    """Test that Router class has expected public methods to prevent accidental renaming."""
    expected_methods = [
        "add_route",
        "get",
        "post",
        "put",
        "delete",
        "patch",
        "head",
        "options",
    ]
    for method in expected_methods:
        assert hasattr(Router, method), f"Router is missing method: {method}"
        assert callable(getattr(Router, method)), f"Router.{method} is not callable"
