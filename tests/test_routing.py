from xyra.routing import Router


def test_router_creation():
    router = Router()
    assert router is not None


def test_router_add_route():
    router = Router()
    router.add_route("GET", "/", lambda: "test")
    assert len(router.routes) == 1


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
