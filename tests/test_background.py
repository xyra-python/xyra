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
        create_background_task(send_email, email)
        # In FastAPI, background tasks are added to response
        # In our framework, create_background_task already schedules it
        res.json({"message": "Email will be sent"})

    # Mock request
    mock_req = Mock()
    mock_req.get_method.return_value = "POST"
    mock_req.get_url.return_value = "http://localhost:8000/send-email"

    def mock_get_header(key):
        if key.lower() == "content-type":
            return "application/json"
        return None
    mock_req.get_header.side_effect = mock_get_header

    mock_req.for_each_header = Mock(
        side_effect=lambda func: func("content-type", "application/json")
    )

    mock_res = Mock()
    mock_res.get_data = AsyncMock(return_value=b'{"email": "user@example.com"}')

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


@pytest.mark.asyncio
async def test_background_task_completes_independently():
    """Test background task completes independently from the current task."""
    result = []
    task_started = asyncio.Event()

    async def long_running_task():
        task_started.set()
        await asyncio.sleep(0.05)
        result.append("done")

    task = create_background_task(long_running_task)

    # Wait for the background task to start
    await task_started.wait()

    # Background task is still running, result should be empty
    assert result == []

    # Wait for the background task to complete
    await task

    assert result == ["done"]


@pytest.mark.asyncio
async def test_background_task_exception():
    """Test exception in background task doesn't crash the event loop."""
    result = []

    # Temporarily set custom exception handler to avoid noisy logs during test
    loop = asyncio.get_running_loop()
    exceptions = []
    def custom_exception_handler(loop, context):
        exceptions.append(context.get("exception"))

    old_handler = loop.get_exception_handler()
    loop.set_exception_handler(custom_exception_handler)

    try:
        async def failing_task():
            result.append("started")
            raise ValueError("Intentional background error")

        task = create_background_task(failing_task)

        # Wait for task to finish - we have to use asyncio.wait to avoid the exception being re-raised to us
        done, _ = await asyncio.wait([task])

        assert result == ["started"]

        # We can extract the exception from the task
        t = done.pop()
        assert isinstance(t.exception(), ValueError)
        assert str(t.exception()) == "Intentional background error"
    finally:
        loop.set_exception_handler(old_handler)
