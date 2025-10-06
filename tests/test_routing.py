from xyra.routing import Router


def test_router_creation():
    router = Router()
    assert router is not None


def test_router_add_route():
    router = Router()
    router.add_route("GET", "/", lambda: "test")
    assert len(router.routes) == 1
