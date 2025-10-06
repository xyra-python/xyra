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
