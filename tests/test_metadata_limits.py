from unittest.mock import AsyncMock

import httpx

from mcp_search import tools
from mcp_search.excerpt import select_excerpts
from mcp_search.fetcher import FetchError, FetchResult
from mcp_search.metadata_limits import (
    MAX_ENGINE_CHARS,
    MAX_ENGINE_NAME_CHARS,
    MAX_GAP_CHARS,
    MAX_HEADING_CHARS,
    MAX_SNIPPET_CHARS,
    MAX_TITLE_CHARS,
    MAX_UNRESPONSIVE_ENGINES,
    truncate_metadata,
)
from mcp_search.server import mcp


def test_metadata_truncation_is_bounded_and_signaled():
    assert truncate_metadata("short", 10) == "short"
    assert truncate_metadata("abcdef", 4) == "abc…"
    assert len(truncate_metadata("abcdef", 4)) == 4


async def test_search_bounds_untrusted_metadata_and_skips_oversized_url(monkeypatch):
    oversized_url = "https://example.com/" + "u" * tools.MAX_URL_CHARS
    valid_url = "https://example.org/article"

    def respond(_request):
        return httpx.Response(
            200,
            json={
                "results": [
                    {"url": oversized_url, "title": "ignored"},
                    {
                        "url": valid_url,
                        "title": "t" * (MAX_TITLE_CHARS + 100),
                        "content": "s" * (MAX_SNIPPET_CHARS + 100),
                        "engines": ["e" * (MAX_ENGINE_CHARS + 100)],
                    },
                ],
                "unresponsive_engines": [
                    ["n" * (MAX_ENGINE_NAME_CHARS + 100), "timeout"]
                    for _ in range(MAX_UNRESPONSIVE_ENGINES + 10)
                ],
            },
        )

    monkeypatch.setattr(tools, "SEARCH_PAUSE_SECONDS", 0)
    monkeypatch.setattr(
        tools,
        "_searxng_client",
        httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    )

    payload = (await tools.web_search("metadata-boundary-test")).model_dump()
    assert [result["url"] for result in payload["results"]] == [valid_url]
    result = payload["results"][0]
    assert len(result["title"]) == MAX_TITLE_CHARS
    assert len(result["snippet"]) == MAX_SNIPPET_CHARS
    assert len(result["engine"]) == MAX_ENGINE_CHARS
    assert len(payload["unresponsive_engines"]) == MAX_UNRESPONSIVE_ENGINES
    assert all(
        len(name) <= MAX_ENGINE_NAME_CHARS for name in payload["unresponsive_engines"]
    )


async def test_fetch_and_gap_metadata_are_bounded(monkeypatch):
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(
            return_value=FetchResult(
                "https://example.com/",
                "t" * (MAX_TITLE_CHARS + 100),
                "Readable source text. " * 20,
            )
        ),
    )
    fetched = (await tools.web_fetch("https://example.com/")).model_dump()
    assert len(fetched["title"]) == MAX_TITLE_CHARS

    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(side_effect=FetchError("x" * (MAX_GAP_CHARS + 500))),
    )
    collected = (
        await tools.research_collect(urls=["https://example.com/"])
    ).model_dump()
    assert len(collected["gaps"][0]) == MAX_GAP_CHARS


def test_heading_cap_preserves_literal_excerpt_offsets():
    heading = "H" * (MAX_HEADING_CHARS + 100)
    text = f"# {heading}\n\n" + "Useful research material. " * 30
    excerpts = select_excerpts(text, ["research"])
    assert excerpts
    excerpt = excerpts[0]
    retained_heading = excerpt["heading"]
    assert retained_heading is not None
    assert len(retained_heading) == MAX_HEADING_CHARS
    assert excerpt["text"] == text[excerpt["start_char"] : excerpt["end_char"]]


async def test_output_schema_advertises_metadata_bounds():
    discovered = {tool.name: tool for tool in await mcp.list_tools()}

    search_defs = discovered["web_search"].outputSchema["$defs"]
    assert (
        search_defs["SearchResult"]["properties"]["title"]["maxLength"]
        == MAX_TITLE_CHARS
    )
    assert (
        search_defs["SearchResult"]["properties"]["snippet"]["maxLength"]
        == MAX_SNIPPET_CHARS
    )
    assert (
        search_defs["SearchResult"]["properties"]["engine"]["maxLength"]
        == MAX_ENGINE_CHARS
    )

    fetch_defs = discovered["web_fetch"].outputSchema["$defs"]
    assert (
        fetch_defs["FetchSuccess"]["properties"]["title"]["maxLength"]
        == MAX_TITLE_CHARS
    )

    collect_defs = discovered["research_collect"].outputSchema["$defs"]
    heading_schema = collect_defs["Excerpt"]["properties"]["heading"]["anyOf"][0]
    assert heading_schema["maxLength"] == MAX_HEADING_CHARS
