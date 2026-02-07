from xyra import libxyra


def test_libxyra_app_creation():
    app = libxyra.App()
    assert app is not None


def test_libxyra_app_methods():
    app = libxyra.App()
    assert hasattr(app, "get")
    assert hasattr(app, "post")
    assert hasattr(app, "put")
    assert hasattr(app, "del")
    assert hasattr(app, "patch")
    assert hasattr(app, "options")
    assert hasattr(app, "head")
    assert hasattr(app, "any")
    assert hasattr(app, "ws")
    assert hasattr(app, "listen")
    assert hasattr(app, "run")


def test_libxyra_request_creation():
    # We can't easily create a uWS::HttpRequest from Python,
    # but we can check if the class exists and has expected methods.
    assert hasattr(libxyra, "Request")
    assert hasattr(libxyra.Request, "get_url")
    assert hasattr(libxyra.Request, "get_method")
    assert hasattr(libxyra.Request, "get_header")
    assert hasattr(libxyra.Request, "get_parameter")
    assert hasattr(libxyra.Request, "get_query")
    assert hasattr(libxyra.Request, "get_headers")


def test_libxyra_response_creation():
    assert hasattr(libxyra, "Response")
    assert hasattr(libxyra.Response, "write_status")
    assert hasattr(libxyra.Response, "write_header")
    assert hasattr(libxyra.Response, "end")
    assert hasattr(libxyra.Response, "on_data")
    assert hasattr(libxyra.Response, "on_aborted")
    assert hasattr(libxyra.Response, "get_remote_address_bytes")


def test_libxyra_websocket_creation():
    assert hasattr(libxyra, "WebSocket")
    assert hasattr(libxyra.WebSocket, "send")
    assert hasattr(libxyra.WebSocket, "close")
