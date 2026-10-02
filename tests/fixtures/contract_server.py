"""Real stdio server with deterministic upstream fixtures, never used in production."""

import httpx

from mcp_search import tools
from mcp_search.fetcher import FetchError, FetchResult
from mcp_search.navigation import PageLink
from mcp_search.security import SecurityError
from mcp_search.server import main

TEXT = "# Research\n\n" + "Evidence about asyncio scheduling and concurrency. " * 80
changing_reads = 0


async def fetch(url: str) -> FetchResult:
    global changing_reads
    if url.startswith("http://127.0.0.1") or url.startswith("https://127.0.0.1"):
        raise SecurityError("loopback/private destinations are blocked")
    if url.endswith("/missing"):
        raise FetchError("HTTP status 404", "choose another source", kind="http_status")
    if url.endswith("/changing"):
        changing_reads += 1
        return FetchResult(url, "Changing text", TEXT + str(changing_reads))
    if url.endswith("/redirect"):
        url = "https://example.com/research"
    links = (
        PageLink(
            "API reference", "https://example.com/api", True, False, None, ("next",)
        ),
        PageLink("Methods", f"{url}#methods", True, True, "methods", ()),
        PageLink(
            "External standard",
            "https://standards.example/spec",
            False,
            False,
            None,
            (),
        ),
    )
    return FetchResult(url, "Fixture title", TEXT, links=links)


def search(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "title": "Fixture title",
                    "url": "https://example.com/research",
                    "content": "Candidate snippet",
                    "engines": ["google"],
                }
            ],
            "unresponsive_engines": [["bing", "timeout"]],
        },
    )


tools.fetch_page = fetch
tools._searxng_client = httpx.AsyncClient(transport=httpx.MockTransport(search))
main()
