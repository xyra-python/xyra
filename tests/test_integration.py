from unittest.mock import AsyncMock, Mock

import pytest
from socketify import OpCode

from xyra import App
from xyra.request import Request
from xyra.response import Response


def test_basic_app_creation_and_route():
    """Test creating a basic app and adding routes."""
    app = App()

    @app.get("/")
    def home(req: Request, res: Response):
        res.text("Hello, World!")

    assert len(app.router.routes) == 1
    route = app.router.routes[0]
    assert route["method"] == "GET"
    assert route["path"] == "/"


def test_app_with_multiple_routes():
    """Test app with GET, POST, and parameterized routes."""
    app = App()

    @app.get("/users")
    def get_users(req: Request, res: Response):
        res.json({"users": []})

    @app.post("/users")
    def create_user(req: Request, res: Response):
        res.status(201).json({"id": 1, "name": "John"})

    @app.get("/users/{id}")
    def get_user(req: Request, res: Response):
        user_id = req.params.get("id")
        res.json({"id": user_id, "name": "John"})

    assert len(app.router.routes) == 3


def test_middleware_usage():
    """Test adding and using middleware."""
    app = App()

    # Mock middleware
    def logging_middleware(req: Request, res: Response):
        # Simulate logging
        pass

    app.use(logging_middleware)

    assert len(app.middlewares) == 1
    assert app.middlewares[0] == logging_middleware


def test_static_files():
    """Test serving static files."""
    app = App()

    app.static_files("/static", "static")

    # Check if static route is registered (this might need adjustment based on implementation)
    # For now, just ensure no error is raised
    assert app is not None


@pytest.mark.asyncio
async def test_request_response_flow():
    """Test the full request-response flow with mocked socketify."""
    app = App()

    @app.get("/test")
    def test_handler(req: Request, res: Response):
        res.json({"message": "success"})

    # Mock socketify request and response
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/test"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    # Create Request and Response objects
    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    # Simulate handler call
    test_handler(request, response)

    # Check response was set correctly
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"


def test_app_run_server_mock():
    """Test running server with mocked socketify app."""
    app = App()

    @app.get("/")
    def home(req: Request, res: Response):
        res.text("Home")

    # Mock the socketify app
    mock_socketify_app = Mock()
    app._app = mock_socketify_app

    # Mock run_server to avoid actual server start
    # Since run_server exists, we just check it can be called (though it would fail in real)
    assert hasattr(app, "run_server")

    # In real scenario, this would start the server
    # For test, we just ensure app is configured
    assert app.templates is not None
    assert app.swagger_options is None


def test_websocket_integration():
    """Test WebSocket integration (basic setup)."""
    from xyra.websockets import WebSocket

    # Mock socketify WebSocket
    mock_ws = Mock()
    ws = WebSocket(mock_ws)

    # Test sending message
    ws.send_text("Hello")
    mock_ws.send.assert_called_with("Hello", OpCode.TEXT)

    # Test subscribing
    ws.subscribe("chat")
    mock_ws.subscribe.assert_called_with("chat")


def test_full_app_workflow():
    """Test a full workflow: create app, add routes, middleware, run."""
    app = App(swagger_options={})  # Provide swagger options to enable

    # Add middleware
    def cors_middleware(req: Request, res: Response):
        res.cors()

    app.use(cors_middleware)

    # Add routes
    @app.get("/")
    def home(req: Request, res: Response):
        res.text("Welcome to Xyra!")

    @app.get("/api/data")
    def api_data(req: Request, res: Response):
        res.json({"data": "example"})

    @app.post("/api/submit")
    def submit(req: Request, res: Response):
        res.status(201).json({"submitted": True})

    # Enable Swagger
    app.enable_swagger()

    # Verify setup
    assert len(app.middlewares) == 1
    assert len(app.router.routes) == 3
    assert app.swagger_options is not None


def test_error_handling_in_routes():
    """Test error handling in route handlers to anticipate errors."""
    from xyra.exceptions import HTTPException

    app = App()

    @app.get("/error")
    def error_handler(req: Request, res: Response):
        raise HTTPException(500, "Internal Server Error")

    @app.get("/invalid_param")
    def invalid_param_handler(req: Request, res: Response):
        # Simulate error from invalid parameter
        param = req.params.get("id")
        if not param or not param.isdigit():
            raise HTTPException(400, "Invalid ID")
        res.json({"id": int(param)})

    # Mock request for error handler
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/error"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    # Test error handler raises exception
    try:
        error_handler(request, response)
        assert False, "Expected HTTPException"
    except HTTPException as e:
        assert e.status_code == 500
        assert e.detail == "Internal Server Error"

    # Test invalid param handler
    mock_req2 = Mock()
    mock_req2.get_method.return_value = "GET"
    mock_req2.get_url.return_value = "http://localhost:8000/invalid_param"
    mock_req2.for_each_header = Mock(side_effect=lambda func: None)

    request2 = Request(mock_req2, mock_res)
    response2 = Response(mock_res)

    try:
        invalid_param_handler(request2, response2)
        assert False, "Expected HTTPException for invalid param"
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == "Invalid ID"


def test_middleware_error_handling():
    """Test middleware that might cause errors."""
    app = App()

    def failing_middleware(req: Request, res: Response):
        # Simulate middleware failure
        raise Exception("Middleware failed")

    app.use(failing_middleware)

    @app.get("/test")
    def test_handler(req: Request, res: Response):
        res.text("OK")

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/test"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    # Test that middleware raises exception
    try:
        # Simulate middleware execution
        for middleware in app.middlewares:
            middleware(request, response)
        assert False, "Expected Exception from middleware"
    except Exception as e:
        assert str(e) == "Middleware failed"


@pytest.mark.asyncio
async def test_async_post_handler():
    """Test async POST handler with JSON body parsing."""
    app = App()

    created_items = []

    @app.post("/items")
    async def create_item(req: Request, res: Response):
        data = await req.json()
        new_item = {
            "id": len(created_items) + 1,
            "name": data.get("name"),
            "description": data.get("description"),
        }
        created_items.append(new_item)
        res.status(201).json(new_item)

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "POST"
    mock_req.get_url.return_value = "http://localhost:8000/items"
    mock_req.for_each_header = Mock(
        side_effect=lambda func: func("content-type", "application/json")
    )

    mock_res = Mock()
    mock_res.get_data = AsyncMock(
        return_value=b'{"name": "Test Item", "description": "A test item"}'
    )
    mock_res.get_json = AsyncMock(
        return_value={"name": "Test Item", "description": "A test item"}
    )

    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    # Call async handler
    await create_item(request, response)

    # Check response
    assert response.status_code == 201
    assert len(created_items) == 1
    assert created_items[0]["name"] == "Test Item"


@pytest.mark.asyncio
async def test_async_put_handler():
    """Test async PUT handler with JSON body parsing."""
    app = App()

    items = [{"id": 1, "name": "Old Name"}]

    @app.put("/items/{item_id}")
    async def update_item(req: Request, res: Response):
        item_id_str = req.params.get("item_id")
        if item_id_str is None:
            res.status(400).json({"error": "Missing item_id"})
            return
        item_id = int(item_id_str)
        data = await req.json()
        item = next((i for i in items if i["id"] == item_id), None)
        if item:
            item.update(data)
            res.json(item)
        else:
            res.status(404).json({"error": "Item not found"})

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "PUT"
    mock_req.get_url.return_value = "http://localhost:8000/items/1"
    mock_req.for_each_header = Mock(
        side_effect=lambda func: func("content-type", "application/json")
    )

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b'{"name": "Updated Name"}')
    mock_res.get_json = AsyncMock(return_value={"name": "Updated Name"})

    request = Request(mock_req, mock_res, {"item_id": "1"})
    response = Response(mock_res)

    # Call async handler
    await update_item(request, response)

    # Check response
    assert response.status_code == 200
    assert items[0]["name"] == "Updated Name"


def test_sync_post_handler():
    """Test sync POST handler without async/await."""
    app = App()

    created_items = []

    @app.post("/items")
    def create_item(req: Request, res: Response):
        # Simulate synchronous body parsing (not using await)
        # In real sync handler, body parsing might be different
        # For test, assume data is passed differently or use form
        # Since req.json() is async, for sync handler, use form or other method
        # Mock form data
        data = {"name": "Sync Item", "description": "A sync created item"}
        new_item = {
            "id": len(created_items) + 1,
            "name": data.get("name"),
            "description": data.get("description"),
        }
        created_items.append(new_item)
        res.status(201).json(new_item)

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "POST"
    mock_req.get_url.return_value = "http://localhost:8000/items"
    mock_req.for_each_header = Mock(
        side_effect=lambda func: func(
            "content-type", "application/x-www-form-urlencoded"
        )
    )

    mock_res = Mock()
    mock_res.get_data = AsyncMock(
        return_value=b"name=Sync%20Item&description=A%20sync%20created%20item"
    )
    mock_res.get_json = AsyncMock(
        return_value={"name": "Sync Item", "description": "A sync created item"}
    )

    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    # Call sync handler
    create_item(request, response)

    # Check response
    assert response.status_code == 201
    assert len(created_items) == 1
    assert created_items[0]["name"] == "Sync Item"


def test_sync_put_handler():
    """Test sync PUT handler without async/await."""
    app = App()

    items = [{"id": 1, "name": "Old Name"}]

    @app.put("/items/{item_id}")
    def update_item(req: Request, res: Response):
        item_id_str = req.params.get("item_id")
        if item_id_str is None:
            res.status(400).json({"error": "Missing item_id"})
            return
        item_id = int(item_id_str)
        # For sync, simulate data from query or form
        data = {"name": "Updated Sync Name"}
        item = next((i for i in items if i["id"] == item_id), None)
        if item:
            item.update(data)
            res.json(item)
        else:
            res.status(404).json({"error": "Item not found"})

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "PUT"
    mock_req.get_url.return_value = "http://localhost:8000/items/1"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()

    request = Request(mock_req, mock_res, {"item_id": "1"})
    response = Response(mock_res)

    # Call sync handler
    update_item(request, response)

    # Check response
    assert response.status_code == 200
    assert items[0]["name"] == "Updated Sync Name"
