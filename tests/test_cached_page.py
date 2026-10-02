import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from unittest.mock import AsyncMock

import httpx
import pytest

from mcp_search import fetcher
from mcp_search.cache import CachedPage, fetch_cache, normalize_url
from mcp_search.navigation import NavigationResult, PageLink


def test_cache_model_import_does_not_load_navigation():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from dataclasses import fields; "
            "from mcp_search.cache import CachedPage; "
            "assert 'mcp_search.navigation' not in sys.modules; "
            "page = CachedPage(url='https://example.com/', title='', text='', "
            "text_truncated=False, links=(), links_truncated=False, text_sufficient=False); "
            "assert len(fields(page)) == 7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("text_sufficient", [False, True])
@pytest.mark.parametrize("text_truncated", [False, True])
@pytest.mark.parametrize("links_truncated", [False, True])
async def test_cached_page_roundtrip_and_redirect_alias(
    monkeypatch, text_sufficient, text_truncated, links_truncated
):
    initial_url = "https://8.8.8.8/start"
    final_url = "https://8.8.8.8/final"
    text = "x" * (fetcher.MIN_EXTRACTED_CHARS + 1 if text_sufficient else 10)
    cap = len(text) - 1 if text_truncated else len(text) + 1
    links = (PageLink("Chapter", final_url + "#chapter", True, True, "chapter", ()),)
    download = AsyncMock(
        return_value=(
            final_url,
            b"<html></html>",
            httpx.Headers({"content-type": "text/html"}),
        )
    )
    extract = AsyncMock(
        return_value=("Title", text, NavigationResult(links, links_truncated))
    )
    monkeypatch.setattr(fetcher, "MAX_TEXT_CHARS", cap)
    monkeypatch.setattr(fetcher, "_download", download)
    monkeypatch.setattr(fetcher, "_extract_bounded", extract)

    fresh = await fetcher.fetch_page(initial_url)
    retained = fetch_cache.get(normalize_url(initial_url))
    assert isinstance(retained, CachedPage)
    assert retained is fetch_cache.get(normalize_url(final_url))
    assert retained == CachedPage(
        url=final_url,
        title="Title",
        text=text[:cap],
        text_truncated=text_truncated,
        links=links,
        links_truncated=links_truncated,
        text_sufficient=text_sufficient,
    )
    assert not hasattr(retained, "cache_hit")
    with pytest.raises(FrozenInstanceError):
        retained.title = "Changed"
    assert not fresh.cache_hit
    for url in (initial_url, final_url):
        cached = await fetcher.fetch_page(url)
        assert cached == replace(fresh, cache_hit=True)
        assert cached.links is retained.links
    download.assert_awaited_once()
    extract.assert_awaited_once()
