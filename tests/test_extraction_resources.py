import asyncio
import threading

import pytest

from mcp_search import fetcher


async def _wait_until(predicate, *, attempts=200):
    for _ in range(attempts):
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition was not reached")


async def test_cancelled_caller_does_not_release_live_extraction_slot(monkeypatch):
    """A cancelled awaiter must not let another parser thread start early."""
    first_started = threading.Event()
    first_release = threading.Event()
    second_started = threading.Event()
    call_lock = threading.Lock()
    calls = 0

    def extract(_html, _base_url):
        nonlocal calls
        with call_lock:
            calls += 1
            call_number = calls
        if call_number == 1:
            first_started.set()
            first_release.wait(timeout=5)
        else:
            second_started.set()
        return (
            "Title",
            "Readable research material. " * 10,
            fetcher.NavigationResult((), False),
        )

    monkeypatch.setattr(fetcher, "EXTRACT_CONCURRENCY", 1)
    monkeypatch.setattr(fetcher, "_extract_executor", None)
    monkeypatch.setattr(fetcher, "_extract_slots", None)
    monkeypatch.setattr(fetcher, "_extract", extract)

    first = asyncio.create_task(
        fetcher._extract_bounded("<p>first</p>", "https://example.com/first")
    )
    second = None
    try:
        await _wait_until(first_started.is_set)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first

        second = asyncio.create_task(
            fetcher._extract_bounded("<p>second</p>", "https://example.com/second")
        )
        await asyncio.sleep(0.05)
        assert not second_started.is_set()

        first_release.set()
        await _wait_until(second_started.is_set)
        title, text, navigation = await second
        assert title == "Title"
        assert text == "Readable research material. " * 10
        assert navigation == fetcher.NavigationResult((), False)
    finally:
        first_release.set()
        if second is not None and not second.done():
            second.cancel()
        await fetcher.close_http_client()


def test_extraction_executor_uses_configured_worker_cap(monkeypatch):
    monkeypatch.setattr(fetcher, "EXTRACT_CONCURRENCY", 2)
    monkeypatch.setattr(fetcher, "_extract_executor", None)
    executor = fetcher._get_extract_executor()
    try:
        assert executor._max_workers == 2
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        monkeypatch.setattr(fetcher, "_extract_executor", None)
