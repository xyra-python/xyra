from xyra.exceptions import (
    ConfigurationException,
    HTTPException,
    MiddlewareException,
    RouteException,
    TemplateException,
    ValidationException,
    WebSocketException,
    XyraException,
    bad_request,
    conflict,
    forbidden,
    internal_server_error,
    method_not_allowed,
    not_found,
    not_implemented,
    service_unavailable,
    too_many_requests,
    unauthorized,
    unprocessable_entity,
)


def test_xyra_exception():
    exc = XyraException("Test error")
    assert str(exc) == "Test error"
    assert exc.message == "Test error"


def test_http_exception():
    exc = HTTPException(404, "Custom not found")
    assert exc.status_code == 404
    assert exc.detail == "Custom not found"
    assert exc.headers == {}
    assert str(exc) == "404: Custom not found"


def test_http_exception_default_detail():
    exc = HTTPException(404)
    assert exc.detail == "Not Found"


def test_http_exception_with_headers():
    headers = {"Content-Type": "application/json"}
    exc = HTTPException(400, "Bad", headers)
    assert exc.headers == headers


def test_websocket_exception():
    exc = WebSocketException(1000, "Normal close")
    assert exc.code == 1000
    assert exc.reason == "Normal close"
    assert str(exc) == "WebSocket Error 1000: Normal close"


def test_websocket_exception_default_reason():
    exc = WebSocketException(1000)
    assert exc.reason == "Normal Closure"


def test_validation_exception():
    errors = {"field": "required"}
    exc = ValidationException("Validation failed", errors)
    assert exc.errors == errors
    assert str(exc) == "Validation failed"


def test_middleware_exception():
    exc = MiddlewareException("Middleware error")
    assert str(exc) == "Middleware error"


def test_template_exception():
    exc = TemplateException("Render error", "index.html")
    assert exc.template_name == "index.html"
    assert str(exc) == "Render error"


def test_route_exception():
    exc = RouteException("Route error")
    assert str(exc) == "Route error"


def test_configuration_exception():
    exc = ConfigurationException("Config error")
    assert str(exc) == "Config error"


def test_bad_request():
    exc = bad_request("Custom bad request")
    assert exc.status_code == 400
    assert exc.detail == "Custom bad request"


def test_unauthorized():
    exc = unauthorized()
    assert exc.status_code == 401
    assert exc.detail == "Unauthorized"


def test_forbidden():
    exc = forbidden()
    assert exc.status_code == 403


def test_not_found():
    exc = not_found()
    assert exc.status_code == 404


def test_method_not_allowed():
    exc = method_not_allowed()
    assert exc.status_code == 405


def test_conflict():
    exc = conflict()
    assert exc.status_code == 409


def test_unprocessable_entity():
    exc = unprocessable_entity()
    assert exc.status_code == 422


def test_too_many_requests():
    exc = too_many_requests()
    assert exc.status_code == 429


def test_internal_server_error():
    exc = internal_server_error()
    assert exc.status_code == 500


def test_not_implemented():
    exc = not_implemented()
    assert exc.status_code == 501


def test_service_unavailable():
    exc = service_unavailable()
    assert exc.status_code == 503
