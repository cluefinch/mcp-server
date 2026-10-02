import httpx
import pytest

from mcp_search import fetcher, tools

REDIRECT_URL = "https://8.8.8.8/redirect"
VALID_URL = "https://1.1.1.1/article"


class ArticleStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b"<html><p>" + b"Useful research evidence. " * 100 + b"</p></html>"


@pytest.fixture
def seen_requests(monkeypatch):
    seen = []

    def respond(request):
        seen.append(str(request.url))
        if str(request.url) == REDIRECT_URL:
            return httpx.Response(302, headers={"location": "https://["})
        assert str(request.url) == VALID_URL
        return httpx.Response(
            200, headers={"content-type": "text/html"}, stream=ArticleStream()
        )

    monkeypatch.setattr(
        fetcher, "_client", httpx.AsyncClient(transport=httpx.MockTransport(respond))
    )
    return seen


async def test_fetch_reports_malformed_redirect(seen_requests):
    with pytest.raises(fetcher.FetchError, match="invalid redirect URL") as caught:
        await fetcher.fetch_page(REDIRECT_URL)
    assert caught.value.kind == "invalid_url"
    assert isinstance(caught.value.__cause__, ValueError)
    assert seen_requests == [REDIRECT_URL]
    assert fetcher.fetch_cache.get(REDIRECT_URL) is None


@pytest.mark.parametrize("tool", [tools.web_fetch, tools.web_links])
async def test_tool_reports_malformed_redirect(seen_requests, tool):
    result = (await tool(REDIRECT_URL)).model_dump()
    assert set(result) == {"error", "hint"}
    assert result["error"] == "invalid redirect URL"
    assert result["hint"]
    assert seen_requests == [REDIRECT_URL]


async def test_collection_keeps_success_alongside_malformed_redirect(seen_requests):
    result = (await tools.research_collect(urls=[REDIRECT_URL, VALID_URL])).model_dump()
    assert [source["url"] for source in result["sources"]] == [VALID_URL]
    assert result["gaps"] == [f"{REDIRECT_URL}: invalid redirect URL"]
    assert sorted(seen_requests) == sorted([REDIRECT_URL, VALID_URL])
