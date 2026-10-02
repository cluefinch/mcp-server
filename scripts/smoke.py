"""Live MCP integration check; requires internet and a running SearXNG."""

import argparse
import asyncio
import json

from mcp_client_test import call_tools


class SmokeTestError(RuntimeError):
    """Raised when the live MCP smoke contract is violated."""


def _require(condition: bool, detail: object) -> None:
    if not condition:
        raise SmokeTestError(str(detail))


def _as_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SmokeTestError(f"{label} is not an object: {value!r}")
    return value


def _as_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise SmokeTestError(f"{label} is not a list: {value!r}")
    return value


async def main(query: str, urls: list[str]) -> None:
    names, results = await call_tools(
        [
            ("web_search", {"query": query, "max_results": 3}),
            ("web_fetch", {"url": urls[0]}),
            ("web_links", {"url": urls[0], "max_links": 5}),
            ("web_fetch", {"url": urls[0]}),
            ("research_collect", {"urls": urls, "max_sources": len(urls)}),
        ]
    )
    _require(
        set(names) == {"web_search", "web_fetch", "web_links", "research_collect"},
        f"Unexpected tool set: {names}",
    )
    if len(results) != 5:
        raise SmokeTestError(f"Expected five tool results, got {len(results)}")

    search = _as_dict(results[0], "Search result")
    first = _as_dict(results[1], "First fetch result")
    links = _as_dict(results[2], "Link result")
    cached = _as_dict(results[3], "Cached fetch result")
    collect = _as_dict(results[4], "Collection result")

    for result in (search, first, links, cached, collect):
        _require("error" not in result, f"Unexpected tool result: {result}")

    search_results = _as_list(search.get("results"), "Search results")
    _require(bool(search_results), search)
    _require(bool(first.get("content") and cached.get("cache_hit")), cached)
    _require(isinstance(links.get("links"), list), links)

    sources = _as_list(collect.get("sources"), "Collection sources")
    _require(len(sources) == len(urls), collect)
    source_objects = [_as_dict(source, "Collection source") for source in sources]
    _require(
        all(
            _as_list(source.get("excerpts"), "Source excerpts")
            for source in source_objects
        ),
        collect,
    )

    print(
        json.dumps(
            {
                "status": "passed",
                "tools": names,
                "search_results": len(search_results),
                "unresponsive_engines": search.get("unresponsive_engines"),
                "sources": [
                    {"url": source.get("url"), "source_id": source.get("source_id")}
                    for source in source_objects
                ],
                "gaps": collect.get("gaps"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="SearXNG documentation")
    parser.add_argument("--url", action="append", dest="urls")
    args = parser.parse_args()
    asyncio.run(
        main(
            args.query,
            args.urls
            or [
                "https://example.com/",
                "https://docs.python.org/3/library/asyncio.html",
            ],
        )
    )
