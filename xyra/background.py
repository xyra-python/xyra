import asyncio


class BackgroundTask:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def __call__(self):
        await self.func(*self.args, **self.kwargs)

def create_background_task(func, *args, **kwargs):
    task = BackgroundTask(func, *args, **kwargs)
    return asyncio.create_task(task())
