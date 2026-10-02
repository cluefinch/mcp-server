from unittest.mock import AsyncMock

from mcp_search import tools
from mcp_search.fetcher import FetchResult
from mcp_search.security import SecurityError


async def test_invalid_credential_url_does_not_suppress_later_valid_url(monkeypatch):
    invalid = "https://user:pass@example.com/article"
    valid = "https://example.com/article"
    calls = []

    async def fetch(url):
        calls.append(url)
        if url == invalid:
            raise SecurityError("credentials in URL not allowed")
        return FetchResult(url, "Title", "Useful research material. " * 20)

    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    result = (
        await tools.research_collect(urls=[invalid, valid], max_sources=2)
    ).model_dump()

    assert calls == [invalid, valid]
    assert [source["url"] for source in result["sources"]] == [valid]
    assert any("blocked_url" in gap for gap in result["gaps"])


async def test_queries_are_not_searched_when_explicit_candidates_fill_budget(
    monkeypatch,
):
    search = AsyncMock(side_effect=AssertionError("search must not run"))
    fetch = AsyncMock(
        side_effect=lambda url: FetchResult(
            url, "Title", "Useful research material. " * 20
        )
    )
    monkeypatch.setattr(tools, "web_search", search)
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)

    urls = ["https://one.example/", "https://two.example/"]
    result = (
        await tools.research_collect(queries=["unused query"], urls=urls, max_sources=2)
    ).model_dump()

    search.assert_not_awaited()
    assert [source["url"] for source in result["sources"]] == urls
    assert result["query_variants"] == ["unused query"]
