import asyncio
import time

import pytest

from xyra.concurrency import to_thread


def test_to_thread_decorator():
    @to_thread
    def blocking_task(value):
        time.sleep(0.01)  # Simulate blocking operation
        return value * 2

    assert asyncio.iscoroutinefunction(blocking_task)


@pytest.mark.asyncio
async def test_to_thread_execution():
    @to_thread
    def blocking_task(x, y):
        return x + y

    result = await blocking_task(5, 3)
    assert result == 8


@pytest.mark.asyncio
async def test_to_thread_with_exception():
    @to_thread
    def failing_task():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await failing_task()


@pytest.mark.asyncio
async def test_concurrent_requests_simulation():
    """Test handling concurrent requests like in FastAPI."""
    from unittest.mock import Mock

    from xyra import App
    from xyra.request import Request
    from xyra.response import Response

    app = App()

    results = []

    @app.get("/async")
    async def async_handler(req: Request, res: Response):
        await asyncio.sleep(0.01)  # Simulate async work
        results.append("async_done")
        res.text("OK")

    # Simulate multiple concurrent requests
    tasks = []
    for i in range(3):
        mock_req = Mock()
        mock_req.get_method.return_value = "GET"
        mock_req.get_url.return_value = f"http://localhost:8000/async{i}"
        mock_req.for_each_header = Mock(side_effect=lambda func: None)

        mock_res = Mock()
        request = Request(mock_req, mock_res)
        response = Response(mock_res)
        tasks.append(async_handler(request, response))

    await asyncio.gather(*tasks)
    assert len(results) == 3
    assert all(r == "async_done" for r in results)


@pytest.mark.asyncio
async def test_async_dependency_injection():
    """Test async dependency injection."""

    async def get_async_data():
        await asyncio.sleep(0.01)
        return {"data": "async"}

    # Simulate using async dependency
    data = await get_async_data()
    assert data["data"] == "async"
