from xyra.routing import Router


def test_router_methods():
    router = Router()

    @router.get("/get")
    def get_handler(req, res):
        pass

    @router.post("/post")
    def post_handler(req, res):
        pass

    @router.put("/put")
    def put_handler(req, res):
        pass

    @router.delete("/delete")
    def delete_handler(req, res):
        pass

    @router.patch("/patch")
    def patch_handler(req, res):
        pass

    @router.head("/head")
    def head_handler(req, res):
        pass

    @router.options("/options")
    def options_handler(req, res):
        pass

    assert len(router.routes) == 7

    methods = {r["method"] for r in router.routes}
    expected_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
    assert methods == expected_methods
