import asyncio
import gzip
from unittest.mock import AsyncMock

import httpx
import pytest

from mcp_search import __version__, fetcher
from mcp_search.security import SecurityError


@pytest.mark.parametrize("override", [None, "", "ResearchClient/1.0"])
async def test_outgoing_user_agent_identity(monkeypatch, override):
    if override is None:
        monkeypatch.delenv("MCP_SEARCH_UA", raising=False)
    else:
        monkeypatch.setenv("MCP_SEARCH_UA", override)
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200)

    monkeypatch.setattr(fetcher, "SafeTransport", lambda: httpx.MockTransport(respond))
    await fetcher._get_client().get("https://example.com/")
    expected = override or (
        f"Cluefinch/{__version__} (+https://github.com/cluefinch/mcp-server)"
    )
    assert requests[0].headers["User-Agent"] == expected


def test_host_interval_default_and_override(monkeypatch):
    monkeypatch.delenv("MCP_SEARCH_HOST_INTERVAL", raising=False)
    monkeypatch.setattr(fetcher, "_limiter", None)
    assert fetcher._get_limiter().interval == 5
    monkeypatch.setenv("MCP_SEARCH_HOST_INTERVAL", "7")
    monkeypatch.setattr(fetcher, "_limiter", None)
    assert fetcher._get_limiter().interval == 7


async def test_redirect_to_private_host_is_blocked(monkeypatch):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(302, headers={"location": "http://127.0.0.1/"})

    monkeypatch.setattr(
        fetcher, "_client", httpx.AsyncClient(transport=httpx.MockTransport(respond))
    )
    with pytest.raises(SecurityError):
        await fetcher._download("https://8.8.8.8/")
    assert len(calls) == 1


@pytest.mark.parametrize("status,headers", [(302, {}), (404, {}), (429, {})])
async def test_http_failures(monkeypatch, status, headers):
    monkeypatch.setattr(
        fetcher,
        "_client",
        httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(status, headers=headers)
            )
        ),
    )
    with pytest.raises(fetcher.FetchError):
        await fetcher._download("https://8.8.8.8/")


async def test_stream_limit(monkeypatch):
    monkeypatch.setattr(fetcher, "MAX_RESPONSE_BYTES", 10)

    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield b"x" * 11

    response = httpx.Response(200, stream=Stream())
    with pytest.raises(fetcher.FetchError):
        await fetcher._read_limited(response)


async def test_extraction_and_cache(monkeypatch):
    html = (
        b"<html><title>Title</title><body><p>"
        + b"Readable research text. " * 20
        + b"</p></body></html>"
    )
    download = AsyncMock(
        return_value=(
            "https://8.8.8.8/",
            html,
            httpx.Headers({"content-type": "text/html"}),
        )
    )
    monkeypatch.setattr(fetcher, "_download", download)
    page = await fetcher.fetch_page("https://8.8.8.8/")
    assert page.title == "Title"
    assert "Readable research" in page.text
    assert (await fetcher.fetch_page("https://8.8.8.8/")).cache_hit
    download.assert_awaited_once()
    with pytest.raises(SecurityError):
        await fetcher.fetch_page("https://user:pass@8.8.8.8/")


async def test_concurrent_identical_fetches_share_one_flight(monkeypatch):
    fetcher.fetch_cache.clear()
    monkeypatch.setattr(fetcher, "_fetch_flights", {})
    validate = AsyncMock(return_value=set())
    monkeypatch.setattr(fetcher, "validate_url", validate)

    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def fetch_uncached(url, key):
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return fetcher.FetchResult(url, "Title", "Useful research material. " * 10)

    monkeypatch.setattr(fetcher, "_fetch_page_uncached", fetch_uncached)

    first = asyncio.create_task(fetcher.fetch_page("https://example.com/article"))
    await started.wait()
    second = asyncio.create_task(fetcher.fetch_page("https://example.com/article"))
    await asyncio.sleep(0)
    release.set()
    first_result, second_result = await asyncio.gather(first, second)

    assert calls == 1
    assert validate.await_count == 2
    assert first_result.text == second_result.text


@pytest.mark.parametrize("size,limit,success", [(200, 300, True), (100000, 300, False)])
async def test_gzip_bounded_output(monkeypatch, size, limit, success):
    monkeypatch.setattr(fetcher, "MAX_RESPONSE_BYTES", limit)

    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield gzip.compress(b"x" * size)

    response = httpx.Response(
        200, headers={"content-encoding": "gzip"}, stream=Stream()
    )
    if success:
        assert await fetcher._read_limited(response) == b"x" * size
    else:
        with pytest.raises(fetcher.FetchError):
            await fetcher._read_limited(response)


@pytest.mark.parametrize(
    "wire_body",
    [
        gzip.compress(b"research payload")[:-8],
        gzip.compress(b"first member") + gzip.compress(b"second member"),
    ],
)
async def test_gzip_rejects_incomplete_and_concatenated_members(wire_body):
    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            yield wire_body

    response = httpx.Response(
        200, headers={"content-encoding": "gzip"}, stream=Stream()
    )

    with pytest.raises(
        fetcher.FetchError, match="incomplete or concatenated gzip response"
    ) as caught:
        await fetcher._read_limited(response)

    assert caught.value.kind == "invalid_content"


def test_html_meta_charset():
    body = '<meta charset="windows-1251"><p>Привет, мир!</p>'.encode("cp1251")
    assert "Привет" in fetcher._decode_html(body, httpx.Headers())


def test_primary_extraction_sets_article_semantics(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        fetcher.trafilatura.metadata, "extract_metadata", lambda html: None
    )

    def extract(html, **kwargs):
        captured.update(kwargs)
        return "x" * fetcher.MIN_EXTRACTED_CHARS

    monkeypatch.setattr(fetcher.trafilatura, "extract", extract)
    fetcher._extract("<p>research</p>", "https://example.com/news/final")

    assert captured["url"] == "https://example.com/news/final"
    assert captured["include_comments"] is False
    assert captured["include_links"] is True


async def test_fetch_page_uses_final_url_as_extraction_base(monkeypatch):
    final_url = "https://8.8.8.8/final/article"
    seen = {}

    monkeypatch.setattr(
        fetcher,
        "_download",
        AsyncMock(
            return_value=(
                final_url,
                b"<p>research</p>",
                httpx.Headers({"content-type": "text/html"}),
            )
        ),
    )

    def extract(html, base_url):
        seen["base_url"] = base_url
        return (
            "Title",
            "x" * fetcher.MIN_EXTRACTED_CHARS,
            fetcher.NavigationResult((), False),
        )

    monkeypatch.setattr(fetcher, "_extract", extract)
    page = await fetcher.fetch_page("https://8.8.8.8/start/article")

    assert page.url == final_url
    assert seen["base_url"] == final_url


async def test_text_truncation_is_disclosed(monkeypatch):
    monkeypatch.setattr(fetcher, "MAX_TEXT_CHARS", 120)
    monkeypatch.setattr(
        fetcher,
        "_download",
        AsyncMock(
            return_value=(
                "https://8.8.8.8/",
                b"<p>" + b"Research material. " * 50 + b"</p>",
                httpx.Headers({"content-type": "text/html"}),
            )
        ),
    )
    first = await fetcher.fetch_page("https://8.8.8.8/")
    second = await fetcher.fetch_page("https://8.8.8.8/")
    assert len(first.text) == 120
    assert first.text_truncated and second.text_truncated


async def test_unsupported_content_is_rejected(monkeypatch):
    monkeypatch.setattr(
        fetcher,
        "_download",
        AsyncMock(
            return_value=(
                "https://8.8.8.8/",
                b"%PDF-1.4",
                httpx.Headers({"content-type": "application/pdf"}),
            )
        ),
    )
    with pytest.raises(fetcher.FetchError) as caught:
        await fetcher.fetch_page("https://8.8.8.8/")
    assert caught.value.kind == "unsupported_content"


async def test_short_html_is_retained_for_non_text_consumers(monkeypatch):
    monkeypatch.setattr(
        fetcher,
        "_download",
        AsyncMock(
            return_value=(
                "https://8.8.8.8/",
                b"<body><script>run()</script></body>",
                httpx.Headers({"content-type": "text/html"}),
            )
        ),
    )
    page = await fetcher.fetch_page("https://8.8.8.8/")
    assert len(page.text) < fetcher.MIN_EXTRACTED_CHARS
