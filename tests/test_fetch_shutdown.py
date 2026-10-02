import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from mcp_search import fetcher

URL = "https://8.8.8.8/shutdown"


@pytest.mark.parametrize("cancel_waiter", [False, True])
async def test_shutdown_drains_fetch_before_closing_resources(
    monkeypatch, cancel_waiter
):
    started = asyncio.Event()
    events = []

    async def fetch(url, key):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            await asyncio.sleep(0)
            events.append("fetch cleaned")

    async def close():
        events.append("client closed")

    executor = Mock()
    executor.shutdown.side_effect = lambda **kwargs: events.append("executor closed")
    monkeypatch.setattr(fetcher, "_fetch_page_uncached", fetch)
    monkeypatch.setattr(
        fetcher, "_client", SimpleNamespace(is_closed=False, aclose=close)
    )
    monkeypatch.setattr(fetcher, "_extract_executor", executor)
    waiter = asyncio.create_task(fetcher.fetch_page(URL))
    try:
        await asyncio.wait_for(started.wait(), 1)
        if cancel_waiter:
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
        await fetcher.close_http_client()
        assert events == ["fetch cleaned", "client closed", "executor closed"]
        assert not fetcher._fetch_flights
        assert fetcher._client is None
        assert fetcher._extract_executor is None
        with pytest.raises(asyncio.CancelledError):
            await waiter
    finally:
        for task in list(fetcher._fetch_flights.values()):
            task.cancel()
        waiter.cancel()
        await asyncio.gather(waiter, return_exceptions=True)


async def test_close_failure_still_drains_tasks_and_shuts_executor(monkeypatch):
    started = asyncio.Event()
    cleaned = asyncio.Event()

    async def fetch(url, key):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    close = AsyncMock(side_effect=RuntimeError("close failed"))
    executor = Mock()
    monkeypatch.setattr(fetcher, "_fetch_page_uncached", fetch)
    monkeypatch.setattr(
        fetcher, "_client", SimpleNamespace(is_closed=False, aclose=close)
    )
    monkeypatch.setattr(fetcher, "_extract_executor", executor)
    waiter = asyncio.create_task(fetcher.fetch_page(URL))
    await asyncio.wait_for(started.wait(), 1)
    with pytest.raises(RuntimeError, match="close failed"):
        await fetcher.close_http_client()
    await asyncio.gather(waiter, return_exceptions=True)
    assert cleaned.is_set()
    executor.shutdown.assert_called_once_with(wait=False, cancel_futures=True)
    assert fetcher._client is None and fetcher._extract_executor is None
    await fetcher.close_http_client()
    close.assert_awaited_once()


async def test_concurrent_and_cancelled_close_waiters_share_cleanup(monkeypatch):
    closing = asyncio.Event()
    release = asyncio.Event()
    closed = asyncio.Event()

    async def close():
        closing.set()
        await release.wait()
        closed.set()

    client = SimpleNamespace(is_closed=False, aclose=AsyncMock(side_effect=close))
    monkeypatch.setattr(fetcher, "_client", client)
    first = asyncio.create_task(fetcher.close_http_client())
    second = None
    try:
        await asyncio.wait_for(closing.wait(), 1)
        second = asyncio.create_task(fetcher.close_http_client())
        await asyncio.sleep(0)
        assert not second.done()
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        assert not closed.is_set()
        release.set()
        await asyncio.wait_for(second, 1)
        assert closed.is_set()
        client.aclose.assert_awaited_once()
        await fetcher.close_http_client()
        client.aclose.assert_awaited_once()
    finally:
        release.set()
        await asyncio.gather(
            first, *([second] if second else []), return_exceptions=True
        )


async def test_teardown_blocks_resource_creation_and_new_fetches(monkeypatch):
    closing = asyncio.Event()
    release = asyncio.Event()

    async def close():
        closing.set()
        await release.wait()

    monkeypatch.setattr(
        fetcher, "_client", SimpleNamespace(is_closed=False, aclose=close)
    )
    shutdown = asyncio.create_task(fetcher.close_http_client())
    try:
        await asyncio.wait_for(closing.wait(), 1)
        for getter in (
            fetcher._get_client,
            fetcher._get_limiter,
            fetcher._get_extract_executor,
            fetcher._get_extract_slots,
        ):
            with pytest.raises(fetcher.FetchError, match="shutting down"):
                getter()
        with pytest.raises(fetcher.FetchError, match="shutting down"):
            await fetcher.fetch_page(URL)
    finally:
        release.set()
        await asyncio.wait_for(shutdown, 1)
    # A new lifecycle can still initialize resources after shutdown completes.
    assert not fetcher._get_client().is_closed


async def test_validation_started_before_shutdown_cannot_restart_fetch(monkeypatch):
    validating = asyncio.Event()
    release = asyncio.Event()

    async def validate(url):
        validating.set()
        await release.wait()
        return set()

    fetch = AsyncMock()
    monkeypatch.setattr(fetcher, "validate_url", validate)
    monkeypatch.setattr(fetcher, "_fetch_page_uncached", fetch)
    waiter = asyncio.create_task(fetcher.fetch_page(URL))
    try:
        await asyncio.wait_for(validating.wait(), 1)
        await fetcher.close_http_client()
        release.set()
        with pytest.raises(fetcher.FetchError, match="shutdown"):
            await asyncio.wait_for(waiter, 1)
        fetch.assert_not_awaited()
    finally:
        release.set()
        await asyncio.gather(waiter, return_exceptions=True)


async def test_completed_flight_during_shutdown_does_not_corrupt_registry(monkeypatch):
    started = asyncio.Event()

    async def fetch(url, key):
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            # A completion can race with cancellation and still produce a result.
            return fetcher.FetchResult(url, "Title", "Research evidence")

    monkeypatch.setattr(fetcher, "_fetch_page_uncached", fetch)
    waiter = asyncio.create_task(fetcher.fetch_page(URL))
    await asyncio.wait_for(started.wait(), 1)
    await fetcher.close_http_client()
    result = await asyncio.wait_for(waiter, 1)
    assert result.url == URL
    assert not fetcher._fetch_flights
    assert fetcher._client is None and fetcher._extract_executor is None


async def test_old_extraction_waiter_cannot_recreate_executor(monkeypatch):
    started = asyncio.Event()
    release = threading.Event()
    loop = asyncio.get_running_loop()

    def extract(html, base_url):
        loop.call_soon_threadsafe(started.set)
        if not release.wait(timeout=5):
            raise AssertionError("Test did not release parser thread")
        return "Title", "Research evidence", fetcher.NavigationResult((), False)

    monkeypatch.setattr(fetcher, "EXTRACT_CONCURRENCY", 1)
    monkeypatch.setattr(fetcher, "_extract", extract)
    first = asyncio.create_task(fetcher._extract_bounded("first", URL))
    queued = None
    try:
        await asyncio.wait_for(started.wait(), 1)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        queued = asyncio.create_task(fetcher._extract_bounded("queued", URL))
        await asyncio.sleep(0)
        assert not queued.done()
        await fetcher.close_http_client()
        assert not release.is_set()
        assert fetcher._extract_executor is None
        release.set()
        with pytest.raises(fetcher.FetchError, match="shutdown"):
            await asyncio.wait_for(queued, 1)
        assert fetcher._extract_executor is None
    finally:
        release.set()
        first.cancel()
        if queued is not None:
            queued.cancel()
        await asyncio.gather(
            first, *([queued] if queued else []), return_exceptions=True
        )
