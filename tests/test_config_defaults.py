import inspect

from mcp_search import cache, fetcher, tools
from mcp_search.config import (
    DEFAULT_FETCH_CONCURRENCY,
    DEFAULT_HOST_INTERVAL,
    DEFAULT_SEARXNG_URL,
    RUNTIME_DEFAULTS,
)
from mcp_search.limits import RequestLimiter


def test_runtime_defaults_are_centralized(monkeypatch):
    assert dict(RUNTIME_DEFAULTS) == {
        "SEARXNG_URL": "http://127.0.0.1:8081",
        "ENGINES": ("google", "google cse", "brave", "wikipedia", "wikidata"),
        "MAX_RESULTS": 20,
        "MAX_FETCH_CHARS": 20_000,
        "MAX_SOURCES": 10,
        "MAX_QUERIES": 10,
        "EXPAND_CHARS": 3000,
        "SEARCH_INTERVAL": 5.0,
        "FETCH_TTL": 600.0,
        "SEARCH_TTL": 300.0,
        "CACHE_ENTRIES": 500,
        "MAX_REDIRECTS": 5,
        "MAX_RESPONSE_BYTES": 5 * 1024 * 1024,
        "MAX_TEXT_CHARS": 100_000,
        "DOWNLOAD_TIMEOUT": 60.0,
        "EXTRACT_CONCURRENCY": 2,
        "MIN_EXTRACTED_CHARS": 100,
        "FETCH_CONCURRENCY": 3,
        "HOST_INTERVAL": 5.0,
    }
    for module, names in {
        cache: ("DEFAULT_FETCH_TTL", "DEFAULT_SEARCH_TTL", "DEFAULT_CACHE_ENTRIES"),
        fetcher: (
            "DEFAULT_MAX_REDIRECTS",
            "DEFAULT_MAX_RESPONSE_BYTES",
            "DEFAULT_MAX_TEXT_CHARS",
            "DEFAULT_DOWNLOAD_TIMEOUT",
            "DEFAULT_EXTRACT_CONCURRENCY",
            "DEFAULT_MIN_EXTRACTED_CHARS",
            "DEFAULT_FETCH_CONCURRENCY",
            "DEFAULT_HOST_INTERVAL",
        ),
        tools: (
            "DEFAULT_ENGINES",
            "DEFAULT_MAX_RESULTS",
            "DEFAULT_MAX_FETCH_CHARS",
            "DEFAULT_MAX_SOURCES",
            "DEFAULT_MAX_QUERIES",
            "DEFAULT_EXPAND_CHARS",
            "DEFAULT_SEARCH_INTERVAL",
            "DEFAULT_SEARXNG_URL",
        ),
    }.items():
        source = inspect.getsource(module)
        assert all(name in source for name in names)
    monkeypatch.delenv("MCP_SEARCH_SEARXNG_URL", raising=False)
    assert tools._searxng_url() == DEFAULT_SEARXNG_URL
    signature = inspect.signature(RequestLimiter)
    assert signature.parameters["concurrency"].default == DEFAULT_FETCH_CONCURRENCY
    assert signature.parameters["interval"].default == DEFAULT_HOST_INTERVAL
