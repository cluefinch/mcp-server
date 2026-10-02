import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx

from mcp_search import tools
from mcp_search.fetcher import FetchResult
from mcp_search.models import SearchSuccess


async def test_search_pause_after_completion_and_failure(monkeypatch):
    clock = [100.0]
    starts = []
    pauses = []

    async def sleep(delay):
        pauses.append(delay)
        clock[0] += delay

    def respond(request):
        starts.append(clock[0])
        clock[0] += 2  # Simulated time spent waiting for SearXNG.
        if request.url.params["q"] == "failure":
            return httpx.Response(503)
        return httpx.Response(200, json={"results": []})

    monkeypatch.setattr(tools, "SEARCH_PAUSE_SECONDS", 5)
    monkeypatch.setattr(tools, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(
        tools, "asyncio", SimpleNamespace(sleep=sleep, Lock=asyncio.Lock)
    )
    monkeypatch.setattr(
        tools,
        "_searxng_client",
        httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    )
    await tools.web_search("first")
    await tools.web_search("first")  # Cache hit must not wait or send a request.
    await tools.web_search("failure")
    await tools.web_search("last")
    assert starts == [100, 107, 114]
    assert pauses == [5, 5]


async def test_search_dedup_cache_and_errors(monkeypatch):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {"url": "https://example.com/#a"},
                    {"url": "https://example.com/#b"},
                    {"url": "https://other.example/"},
                ],
                "unresponsive_engines": [["bing", "timeout"]],
            },
        )

    monkeypatch.setattr(
        tools,
        "_searxng_client",
        httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    )
    result = (await tools.web_search("test", max_results=2, safe_search=0)).model_dump()
    assert len(result["results"]) == 2
    assert result["unresponsive_engines"] == ["bing"]
    assert calls[0].url.params["safe_search"] == "0"
    cached = (await tools.web_search("test", max_results=2, safe_search=0)).root
    assert isinstance(cached, SearchSuccess)
    assert cached.cached
    assert len(calls) == 1


async def test_pagination_reconstructs_exact_text(monkeypatch):
    text = ("abc " * 25 + "\n\n") * 9
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(return_value=FetchResult("https://example.com", "Title", text)),
    )
    offset = 0
    pieces = []
    while True:
        result = (
            await tools.web_fetch("https://example.com", offset, 170)
        ).model_dump()
        pieces.append(result["content"])
        if not result["truncated"]:
            break
        assert result["next_start"] > offset
        offset = result["next_start"]
    assert "".join(pieces) == text


async def test_collection_fairness_and_engine_gaps(monkeypatch):
    async def search(query, **_kwargs):
        return tools.SearchResponse.model_validate(
            {
                "results": [
                    {
                        "url": f"https://{query}.example/{i}",
                        "title": "",
                        "snippet": "",
                        "engine": "",
                        "source_type": "unknown",
                    }
                    for i in range(3)
                ],
                "unresponsive_engines": ["bing"],
                "query_used": query,
                "cached": False,
            }
        )

    async def fetch(url):
        return FetchResult(url, "Title", "Useful research material. " * 10)

    monkeypatch.setattr(tools, "web_search", search)
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    result = (
        await tools.research_collect(
            queries=["first", "second"],
            urls=["https://explicit.example/"],
            max_sources=3,
        )
    ).model_dump()
    assert [s["url"] for s in result["sources"]] == [
        "https://explicit.example/",
        "https://first.example/0",
        "https://second.example/0",
    ]
    assert len(result["gaps"]) == 2
    assert all("bing" in gap for gap in result["gaps"])


async def test_full_explicit_budget_skips_search(monkeypatch):
    search = AsyncMock()
    fetch = AsyncMock(
        return_value=FetchResult(
            "https://explicit.example/", "Title", "Useful research material. " * 10
        )
    )
    monkeypatch.setattr(tools, "web_search", search)
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)

    result = (
        await tools.research_collect(
            queries=["unused query"], urls=["https://explicit.example/"], max_sources=1
        )
    ).model_dump()

    search.assert_not_awaited()
    fetch.assert_awaited_once_with("https://explicit.example/")
    assert result["query_variants"] == ["unused query"]
    assert [source["url"] for source in result["sources"]] == [
        "https://explicit.example/"
    ]


async def test_invalid_explicit_variant_does_not_suppress_valid_url(monkeypatch):
    async def fetch(url):
        if "user:pass@" in url:
            raise tools.SecurityError("credentials in URL not allowed")
        return FetchResult(
            "https://example.com/article", "Title", "Useful research material. " * 10
        )

    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    result = (
        await tools.research_collect(
            urls=[
                "https://user:pass@example.com/article",
                "https://example.com/article",
            ],
            max_sources=2,
        )
    ).model_dump()

    assert [source["url"] for source in result["sources"]] == [
        "https://example.com/article"
    ]
    assert len(result["gaps"]) == 1
    assert "blocked_url" in result["gaps"][0]


async def test_redirect_duplicates(monkeypatch):
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(
            return_value=FetchResult(
                "https://example.com/final", "Title", "Useful text. " * 20
            )
        ),
    )
    result = (
        await tools.research_collect(
            urls=["https://example.com/a", "https://example.com/b"]
        )
    ).model_dump()
    assert len(result["sources"]) == 1
    assert "same final document" in result["gaps"][0]
    assert result["sources"][0]["source_id"] == tools._source_id(
        "https://example.com/final#x"
    )
