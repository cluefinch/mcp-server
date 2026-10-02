import pytest

from mcp_search import fetcher, tools
from mcp_search.cache import fetch_cache, search_cache


@pytest.fixture(autouse=True)
async def isolated_state(monkeypatch):
    fetch_cache.clear()
    search_cache.clear()
    monkeypatch.setattr(tools, "_search_lock", None)
    monkeypatch.setattr(tools, "_last_search_at", 0)
    monkeypatch.setattr(tools, "SEARCH_PAUSE_SECONDS", 0)
    yield
    await fetcher.close_http_client()
    await tools.close_searxng_client()
