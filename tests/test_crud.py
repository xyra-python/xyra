import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from xyra import App
from xyra.request import Request
from xyra.response import Response

# Mock data store for CRUD operations
users_db = {}


def reset_db():
    global users_db
    users_db = {}


@pytest.fixture(autouse=True)
def setup_and_teardown():
    reset_db()
    yield
    reset_db()


# Sync CRUD handlers
def get_users_sync(req: Request, res: Response):
    res.json(list(users_db.values()))


def get_user_sync(req: Request, res: Response):
    user_id = req.params.get("id")
    if user_id in users_db:
        res.json(users_db[user_id])
    else:
        res.status(404).json({"error": "User not found"})


def create_user_sync(req: Request, res: Response):
    # In real app, parse JSON from request
    new_user = {"id": len(users_db) + 1, "name": "New User", "email": "new@example.com"}
    users_db[str(new_user["id"])] = new_user
    res.status(201).json(new_user)


def update_user_sync(req: Request, res: Response):
    user_id = req.params.get("id")
    if user_id in users_db:
        # In real app, parse JSON from request
        users_db[user_id]["name"] = "Updated User"
        res.json(users_db[user_id])
    else:
        res.status(404).json({"error": "User not found"})


def delete_user_sync(req: Request, res: Response):
    user_id = req.params.get("id")
    if user_id in users_db:
        deleted_user = users_db.pop(user_id)
        res.json({"message": "User deleted", "user": deleted_user})
    else:
        res.status(404).json({"error": "User not found"})


# Async CRUD handlers
async def get_users_async(req: Request, res: Response):
    # Simulate async operation
    await asyncio.sleep(0.01)
    res.json(list(users_db.values()))


async def get_user_async(req: Request, res: Response):
    user_id = req.params.get("id")
    # Simulate async operation
    await asyncio.sleep(0.01)
    if user_id in users_db:
        res.json(users_db[user_id])
    else:
        res.status(404).json({"error": "User not found"})


async def create_user_async(req: Request, res: Response):
    # Simulate async operation
    await asyncio.sleep(0.01)
    new_user = {
        "id": len(users_db) + 1,
        "name": "New User Async",
        "email": "newasync@example.com",
    }
    users_db[str(new_user["id"])] = new_user
    res.status(201).json(new_user)


async def update_user_async(req: Request, res: Response):
    user_id = req.params.get("id")
    # Simulate async operation
    await asyncio.sleep(0.01)
    if user_id in users_db:
        users_db[user_id]["name"] = "Updated User Async"
        res.json(users_db[user_id])
    else:
        res.status(404).json({"error": "User not found"})


async def delete_user_async(req: Request, res: Response):
    user_id = req.params.get("id")
    # Simulate async operation
    await asyncio.sleep(0.01)
    if user_id in users_db:
        deleted_user = users_db.pop(user_id)
        res.json({"message": "User deleted", "user": deleted_user})
    else:
        res.status(404).json({"error": "User not found"})


def create_crud_app(sync=True):
    app = App()
    if sync:
        app.get("/users", get_users_sync)
        app.get("/users/{id}", get_user_sync)
        app.post("/users", create_user_sync)
        app.put("/users/{id}", update_user_sync)
        app.delete("/users/{id}", delete_user_sync)
    else:
        app.get("/users", get_users_async)
        app.get("/users/{id}", get_user_async)
        app.post("/users", create_user_async)
        app.put("/users/{id}", update_user_async)
        app.delete("/users/{id}", delete_user_async)
    return app


@pytest.mark.parametrize("sync", [True, False])
def test_crud_get_users_empty(sync):
    app = create_crud_app(sync)
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/users"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    req = Request(mock_req, mock_res)
    res = Response(mock_res)

    # Find and call the handler
    route = next(
        r for r in app.router.routes if r["path"] == "/users" and r["method"] == "GET"
    )
    if sync:
        route["handler"](req, res)
    else:
        import asyncio

        asyncio.run(route["handler"](req, res))

    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/json"


@pytest.mark.parametrize("sync", [True, False])
def test_crud_create_user(sync):
    app = create_crud_app(sync)
    mock_req = Mock()
    mock_req.get_method.return_value = "POST"
    mock_req.get_url.return_value = "http://localhost:8000/users"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    req = Request(mock_req, mock_res)
    res = Response(mock_res)

    route = next(
        r for r in app.router.routes if r["path"] == "/users" and r["method"] == "POST"
    )
    if sync:
        route["handler"](req, res)
    else:
        import asyncio

        asyncio.run(route["handler"](req, res))

    assert res.status_code == 201


@pytest.mark.parametrize("sync", [True, False])
def test_crud_get_user(sync):
    # Pre-populate db
    users_db["1"] = {"id": 1, "name": "Test User", "email": "test@example.com"}

    app = create_crud_app(sync)
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/users/1"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    req = Request(mock_req, mock_res, {"id": "1"})
    res = Response(mock_res)

    route = next(
        r
        for r in app.router.routes
        if r["path"] == "/users/{id}" and r["method"] == "GET"
    )
    if sync:
        route["handler"](req, res)
    else:
        import asyncio

        asyncio.run(route["handler"](req, res))

    assert res.status_code == 200


@pytest.mark.parametrize("sync", [True, False])
def test_crud_update_user(sync):
    users_db["1"] = {"id": 1, "name": "Test User", "email": "test@example.com"}

    app = create_crud_app(sync)
    mock_req = Mock()
    mock_req.get_method.return_value = "PUT"
    mock_req.get_url.return_value = "http://localhost:8000/users/1"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    req = Request(mock_req, mock_res, {"id": "1"})
    res = Response(mock_res)

    route = next(
        r
        for r in app.router.routes
        if r["path"] == "/users/{id}" and r["method"] == "PUT"
    )
    if sync:
        route["handler"](req, res)
    else:
        import asyncio

        asyncio.run(route["handler"](req, res))

    assert res.status_code == 200
    assert users_db["1"]["name"] == ("Updated User" if sync else "Updated User Async")


@pytest.mark.parametrize("sync", [True, False])
def test_crud_delete_user(sync):
    users_db["1"] = {"id": 1, "name": "Test User", "email": "test@example.com"}

    app = create_crud_app(sync)
    mock_req = Mock()
    mock_req.get_method.return_value = "DELETE"
    mock_req.get_url.return_value = "http://localhost:8000/users/1"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    req = Request(mock_req, mock_res, {"id": "1"})
    res = Response(mock_res)

    route = next(
        r
        for r in app.router.routes
        if r["path"] == "/users/{id}" and r["method"] == "DELETE"
    )
    if sync:
        route["handler"](req, res)
    else:
        import asyncio

        asyncio.run(route["handler"](req, res))

    assert res.status_code == 200
    assert "1" not in users_db


@pytest.mark.parametrize("sync", [True, False])
def test_crud_get_user_not_found(sync):
    app = create_crud_app(sync)
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/users/999"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b"{}")
    mock_res.get_json = AsyncMock(return_value={})

    req = Request(mock_req, mock_res, {"id": "999"})
    res = Response(mock_res)

    route = next(
        r
        for r in app.router.routes
        if r["path"] == "/users/{id}" and r["method"] == "GET"
    )
    if sync:
        route["handler"](req, res)
    else:
        import asyncio

        asyncio.run(route["handler"](req, res))

    assert res.status_code == 404
