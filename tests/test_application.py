from unittest.mock import Mock

from xyra import App
from xyra.request import Request
from xyra.response import Response


def test_app_creation():
    app = App()
    assert app is not None


def test_app_route():
    app = App()

    @app.get("/")
    def home():
        return "Hello"

    assert len(app.router.routes) == 1


def test_app_run():
    app = App()
    # Mock run to avoid actual server start
    assert hasattr(app, "run_server")


def test_404_handler_registration():
    """Test that 404 handler is registered for unmatched routes."""
    app = App()

    # Mock the socketify app
    mock_app = Mock()
    app._app = mock_app

    # Register routes (this should add the 404 handler)
    app._register_routes()

    # Check that any() was called with a catch-all pattern
    mock_app.any.assert_called()
    call_args = mock_app.any.call_args
    assert call_args[0][0] == "/*"  # The pattern should be "/*"


def test_app_api_stability():
    """Test that App class has expected public methods and properties to prevent accidental renaming."""
    expected_methods = [
        "route",
        "get",
        "post",
        "put",
        "delete",
        "patch",
        "head",
        "options",
        "use",
        "static_files",
        "enable_swagger",
        "run_server",
        "listen",
    ]
    expected_properties = ["router", "middlewares"]

    for method in expected_methods:
        assert hasattr(App, method), f"App is missing method: {method}"
        assert callable(getattr(App, method)), f"App.{method} is not callable"

    for prop in expected_properties:
        assert hasattr(App, prop), f"App is missing property: {prop}"


def test_dependency_injection_simulation():
    """Test simulated dependency injection like in FastAPI."""
    from unittest.mock import Mock

    app = App()

    # Mock dependency
    def get_db():
        return {"connection": "mock_db"}

    def get_current_user():
        return {"id": 1, "name": "John"}

    # Simulate injecting dependencies into handler
    @app.get("/users/me")
    def get_user(req, res, db=None, user=None):
        # In real FastAPI, dependencies are injected automatically
        # Here we simulate by passing them
        if db is None:
            db = get_db()
        if user is None:
            user = get_current_user()
        res.json({"user": user, "db_status": db["connection"]})

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/users/me"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    # Call handler with simulated dependencies
    get_user(request, response, db=get_db(), user=get_current_user())

    # Check response
    assert response.status_code == 200
    # Assuming json method sets some internal data
    mock_res.end.assert_called()  # Or whatever response.json does
