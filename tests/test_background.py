import asyncio

import pytest

from xyra.background import BackgroundTask, create_background_task


@pytest.mark.asyncio
async def test_background_task():
    results = []

    async def sample_task(value):
        await asyncio.sleep(0.01)
        results.append(value)

    task = BackgroundTask(sample_task, "test")
    await task()
    assert results == ["test"]


@pytest.mark.asyncio
async def test_create_background_task_execution():
    results = []

    async def sample_task(value):
        await asyncio.sleep(0.01)
        results.append(value)

    task = create_background_task(sample_task, "executed")
    await task
    assert results == ["executed"]


@pytest.mark.asyncio
async def test_background_task_in_route_handler():
    """Test background task used in route handler like FastAPI."""
    from unittest.mock import AsyncMock, Mock

    from xyra import App
    from xyra.request import Request
    from xyra.response import Response

    app = App()

    results = []

    async def send_email(email: str):
        await asyncio.sleep(0.01)
        results.append(f"Email sent to {email}")

    @app.post("/send-email")
    async def send_email_endpoint(req: Request, res: Response):
        data = await req.json()
        email = data.get("email")
        # Simulate adding background task
        task = create_background_task(send_email, email)
        # In FastAPI, background tasks are added to response
        # Here we simulate by awaiting it
        asyncio.create_task(task)
        res.json({"message": "Email will be sent"})

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "POST"
    mock_req.get_url.return_value = "http://localhost:8000/send-email"
    mock_req.for_each_header = Mock(
        side_effect=lambda func: func("content-type", "application/json")
    )

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b'{"email": "user@example.com"}')
    mock_res.get_json = AsyncMock(return_value={"email": "user@example.com"})

    request = Request(mock_req, mock_res)
    response = Response(mock_res)

    await send_email_endpoint(request, response)

    # Wait for background task
    await asyncio.sleep(0.02)
    assert results == ["Email sent to user@example.com"]


@pytest.mark.asyncio
async def test_multiple_background_tasks():
    """Test multiple background tasks running concurrently."""
    results = []

    async def task1():
        await asyncio.sleep(0.01)
        results.append("task1")

    async def task2():
        await asyncio.sleep(0.01)
        results.append("task2")

    tasks = [create_background_task(task1), create_background_task(task2)]
    await asyncio.gather(*tasks)
    assert set(results) == {"task1", "task2"}
