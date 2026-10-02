import httpx
import pytest

from mcp_search import fetcher, tools
from mcp_search.navigation import extract_navigation
from mcp_search.url_limits import MAX_URL_CHARS, exceeds_url_limit

BASE = "https://8.8.8.8/"
EXPANDED_URL = BASE + "é" * 1400


class HTMLStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield (
            b'<html><title>Research</title><a href="/a">A</a>'
            b'<a href="/b">B</a><p>'
            + b"Useful research evidence. " * 100
            + b"</p></html>"
        )


@pytest.fixture
def seen_requests(monkeypatch):
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(
            200, headers={"content-type": "text/html"}, stream=HTMLStream()
        )

    monkeypatch.setattr(
        fetcher, "_client", httpx.AsyncClient(transport=httpx.MockTransport(respond))
    )
    return seen


@pytest.mark.parametrize("extra,expected", [(0, False), (1, True)])
@pytest.mark.parametrize("unicode_path", [False, True])
def test_limit_boundary_in_httpx_representation(extra, expected, unicode_path):
    prefix = BASE + ("é" if unicode_path else "x")
    remaining = MAX_URL_CHARS - len(str(httpx.URL(prefix)))
    url = prefix + "x" * (remaining + extra)
    assert exceeds_url_limit(url) is expected
    assert exceeds_url_limit(str(httpx.URL(url))) is expected


def test_raw_input_cap_is_preserved_when_httpx_shortens_url():
    url = "https://8.8.8.8:443/" + "x" * (MAX_URL_CHARS - len(BASE))
    assert len(str(httpx.URL(url))) == MAX_URL_CHARS
    assert exceeds_url_limit(url)


@pytest.mark.parametrize("suffix", ["é" * 1400, "#" + "é" * 1400])
async def test_expanded_input_fails_before_cache_or_network(seen_requests, suffix):
    url = BASE + suffix
    assert len(url) < MAX_URL_CHARS
    # A fragment-only variant shares the cache key with this valid document.
    await fetcher.fetch_page(BASE)
    seen_requests.clear()
    with pytest.raises(fetcher.FetchError, match="HTTPX representation") as caught:
        await fetcher.fetch_page(url)
    assert caught.value.kind == "invalid_url"
    assert seen_requests == []


@pytest.mark.parametrize("tool", [tools.web_fetch, tools.web_links])
async def test_tools_report_expansion_as_structured_error(seen_requests, tool):
    result = (await tool(EXPANDED_URL)).model_dump()
    assert set(result) == {"error", "hint"}
    assert "8192" in result["error"]
    assert seen_requests == []


@pytest.mark.parametrize(
    "target", [BASE + "x" * MAX_URL_CHARS, str(httpx.URL(EXPANDED_URL))]
)
async def test_oversized_redirect_is_not_requested(monkeypatch, target):
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(302, headers={"location": target})

    monkeypatch.setattr(
        fetcher, "_client", httpx.AsyncClient(transport=httpx.MockTransport(respond))
    )
    result = (await tools.web_links(BASE)).model_dump()
    assert "8192" in result["error"]
    assert len(seen) == 1
    assert fetcher.fetch_cache.get(BASE) is None


async def test_collection_keeps_valid_source_and_reports_expansion_gap(seen_requests):
    result = (await tools.research_collect(urls=[EXPANDED_URL, BASE])).model_dump()
    assert len(result["sources"]) == 1
    assert result["sources"][0]["url"] == BASE
    assert any("8192" in gap for gap in result["gaps"])
    assert len(seen_requests) == 1
    expanded = (
        await tools.web_fetch(
            **result["sources"][0]["excerpts"][0]["expand"]["arguments"]
        )
    ).model_dump()
    assert "error" not in expanded


async def test_boundary_final_url_and_ready_continuations(seen_requests):
    prefix = BASE + "é"
    url = prefix + "x" * (MAX_URL_CHARS - len(str(httpx.URL(prefix))))
    first = (await tools.web_fetch(url, max_chars=100)).model_dump()
    assert len(first["url"]) == MAX_URL_CHARS
    second = (await tools.web_fetch(**first["continuation"]["arguments"])).model_dump()
    assert "error" not in second
    assert second["cache_hit"]
    links = (await tools.web_links(first["url"], max_links=1)).model_dump()
    more_links = (
        await tools.web_links(**links["continuation"]["arguments"])
    ).model_dump()
    assert "error" not in more_links
    assert more_links["cache_hit"]
    assert len(seen_requests) == 1


def test_navigation_drops_links_exceeding_encoded_budget():
    result = extract_navigation(
        f'<a href="{EXPANDED_URL}">Long</a><a href="/valid">Valid</a>', BASE
    )
    assert [link.url for link in result.links] == [BASE + "valid"]
    assert result.links_truncated


def test_oversized_encoded_base_falls_back_to_final_url():
    result = extract_navigation(
        f'<base href="{EXPANDED_URL}/"><a href="child">Child</a>', BASE
    )
    assert [link.url for link in result.links] == [BASE + "child"]
    assert not result.links_truncated
