import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from mcp_search import fetcher
from mcp_search.security import SecurityError


async def test_concurrent_identical_fetches_share_one_download(monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0
    html = (
        b"<html><title>Title</title><body><p>"
        + b"research " * 40
        + b"</p></body></html>"
    )

    async def download(url, *, validate_initial=True):
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return url, html, httpx.Headers({"content-type": "text/html"})

    monkeypatch.setattr(fetcher, "_download", download)

    first = asyncio.create_task(fetcher.fetch_page("https://8.8.8.8/article"))
    await started.wait()
    second = asyncio.create_task(fetcher.fetch_page("https://8.8.8.8/article"))
    await asyncio.sleep(0)
    release.set()

    one, two = await asyncio.gather(first, second)
    assert calls == 1
    assert one.text == two.text
    assert not one.cache_hit and not two.cache_hit

    cached = await fetcher.fetch_page("https://8.8.8.8/article")
    assert cached.cache_hit
    assert calls == 1


async def test_cancelled_waiter_does_not_cancel_shared_fetch(monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0
    html = b"<p>" + b"research " * 40 + b"</p>"

    async def download(url, *, validate_initial=True):
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return url, html, httpx.Headers({"content-type": "text/html"})

    monkeypatch.setattr(fetcher, "_download", download)

    first = asyncio.create_task(fetcher.fetch_page("https://8.8.8.8/shared"))
    await started.wait()
    second = asyncio.create_task(fetcher.fetch_page("https://8.8.8.8/shared"))
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first

    release.set()
    result = await second
    assert "research" in result.text
    assert calls == 1


async def test_each_caller_is_validated_before_single_flight_lookup(monkeypatch):
    download = AsyncMock()
    monkeypatch.setattr(fetcher, "_download", download)

    with pytest.raises(SecurityError):
        await fetcher.fetch_page("https://user:pass@8.8.8.8/article")

    download.assert_not_awaited()
