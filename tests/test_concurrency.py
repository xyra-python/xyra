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
