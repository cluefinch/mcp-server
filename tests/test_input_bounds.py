from unittest.mock import AsyncMock

from mcp_search import tools
from mcp_search.server import mcp


async def test_mcp_discovery_exposes_input_safety_bounds():
    discovered = {tool.name: tool for tool in await mcp.list_tools()}

    search = discovered["web_search"].inputSchema["properties"]
    assert search["query"]["maxLength"] == tools.MAX_QUERY_CHARS
    assert search["engines"]["anyOf"][0]["maxItems"] == len(tools.VALID_ENGINES)
    assert search["language"]["anyOf"][0]["maxLength"] == tools.MAX_LANGUAGE_CHARS
    assert search["domain"]["anyOf"][0]["maxLength"] == tools.MAX_DOMAIN_CHARS
    excluded = search["exclude_domains"]["anyOf"][0]
    assert excluded["maxItems"] == tools.MAX_DOMAIN_FILTERS
    assert excluded["items"]["maxLength"] == tools.MAX_DOMAIN_CHARS

    fetch = discovered["web_fetch"].inputSchema["properties"]
    assert fetch["url"]["maxLength"] == tools.MAX_URL_CHARS

    collect = discovered["research_collect"].inputSchema["properties"]
    assert collect["topic"]["anyOf"][0]["maxLength"] == tools.MAX_TOPIC_CHARS
    queries = collect["queries"]["anyOf"][0]
    assert queries["maxItems"] == tools.MAX_QUERIES
    assert queries["items"]["maxLength"] == tools.MAX_QUERY_CHARS
    urls = collect["urls"]["anyOf"][0]
    assert urls["maxItems"] == tools.MAX_EXPLICIT_URLS
    assert urls["items"]["maxLength"] == tools.MAX_URL_CHARS


async def test_runtime_rejects_oversized_inputs_before_network(monkeypatch):
    search_client = AsyncMock()
    fetch = AsyncMock()
    monkeypatch.setattr(tools, "_get_searxng_client", lambda: search_client)
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)

    search = await tools.web_search("x" * (tools.MAX_QUERY_CHARS + 1))
    assert search.model_dump()["error"].startswith("query exceeds")

    page = await tools.web_fetch("https://example.com/" + "x" * tools.MAX_URL_CHARS)
    assert page.model_dump()["error"].startswith("url exceeds")

    collected = await tools.research_collect(
        urls=["https://example.com/"] * (tools.MAX_EXPLICIT_URLS + 1)
    )
    assert collected.model_dump()["error"].startswith("at most")

    fetch.assert_not_awaited()
    search_client.get.assert_not_awaited()


def test_explicit_url_input_ceiling_is_separate_from_fetch_budget():
    assert tools.MAX_EXPLICIT_URLS > tools.MAX_SOURCES_CAP
