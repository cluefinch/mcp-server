import asyncio
import time
from itertools import pairwise

from mcp_search.limits import RequestLimiter


async def test_same_host_serialized_and_spaced():
    limiter = RequestLimiter(concurrency=2, interval=0.02)
    starts = []
    active = 0

    async def request():
        nonlocal active
        async with limiter.request("https://example.com/"):
            assert active == 0
            active += 1
            starts.append(time.monotonic())
            await asyncio.sleep(0)
            active -= 1

    await asyncio.gather(request(), request(), request())
    assert all(b - a >= 0.019 for a, b in pairwise(starts))
    async with asyncio.timeout(1):
        while limiter.hosts:
            await asyncio.sleep(0.01)
    assert not limiter.hosts


async def test_cancelled_waiter_releases_host_state():
    limiter = RequestLimiter(concurrency=1, interval=0.001)
    async with limiter.request("https://example.com/"):

        async def wait():
            async with limiter.request("https://example.com/"):
                raise AssertionError("cancelled waiter entered")

        task = asyncio.create_task(wait())
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    async with asyncio.timeout(1):
        while limiter.hosts:
            await asyncio.sleep(0.01)
    assert not limiter.hosts
