import asyncio
from hashlib import sha256
from unittest.mock import AsyncMock

import httpx

from mcp_search import fetcher, navigation, tools
from mcp_search.cache import TTLCache
from mcp_search.fetcher import FetchResult
from mcp_search.navigation import PageLink, extract_navigation, links_hash


def test_navigation_resolves_base_labels_fragments_and_deduplicates():
    html = """
    <html><head><base href="/docs/"></head><body>
      <a href="chapter#intro"> Chapter   One </a>
      <a href="chapter#intro" rel="next">Duplicate</a>
      <a href="#local" aria-label="Local section"></a>
      <a href="https://other.example/x"><img alt="External source"></a>
      <a href="mailto:test@example.com">Mail</a>
    </body></html>
    """
    result = extract_navigation(html, "https://example.com/start/index.html")
    assert result.links_truncated is False
    assert [link.url for link in result.links] == [
        "https://example.com/docs/chapter#intro",
        "https://example.com/docs/#local",
        "https://other.example/x",
    ]
    first = result.links[0]
    assert first.label == "Chapter One"
    assert first.rel == ("next",)
    assert first.same_origin is True and first.same_document is False
    assert result.links[1].fragment == "local"
    assert result.links[2].label == "External source"
    assert result.links[2].same_origin is False


def test_discovery_does_not_approve_private_destination():
    result = extract_navigation(
        '<a href="http://127.0.0.1/private">internal</a>', "https://example.com/"
    )
    assert result.links[0].url == "http://127.0.0.1/private"


def test_origin_uses_effective_port_and_fragment_preserves_document_identity():
    result = extract_navigation(
        """
        <a href="https://example.com:443/report#methods">Methods</a>
        <a href="http://example.com/report">HTTP copy</a>
        """,
        "https://example.com/report",
    )
    secure, insecure = result.links
    assert secure.same_origin is True
    assert secure.same_document is True
    assert secure.fragment == "methods"
    assert insecure.same_origin is False
    assert insecure.same_document is False


def test_navigation_limits_disclose_lost_links(monkeypatch):
    monkeypatch.setattr(navigation, "MAX_RETAINED_LINKS", 2)
    result = extract_navigation(
        '<a href="/a">A</a><a href="/b">B</a><a href="/c">C</a>', "https://example.com/"
    )
    assert [link.label for link in result.links] == ["A", "B"]
    assert result.links_truncated is True


def test_overlong_url_is_dropped_and_disclosed():
    href = "https://example.com/" + "x" * navigation.MAX_URL_CHARS
    result = extract_navigation(
        f'<a href="{href}">Too long</a>', "https://example.com/"
    )
    assert result.links == ()
    assert result.links_truncated is True


def test_credentials_are_rejected_not_normalized():
    result = extract_navigation(
        '<a href="https://user:pass@example.com/private">Private</a>',
        "https://example.com/",
    )
    assert result.links == ()
    assert result.links_truncated is False


def test_duplicate_can_improve_label_without_moving_entry():
    result = extract_navigation(
        '<a href="/chapter"></a><a href="/other">Other</a>'
        '<a href="/chapter" aria-label="Chapter"></a>',
        "https://example.com/",
    )
    assert [link.url for link in result.links] == [
        "https://example.com/chapter",
        "https://example.com/other",
    ]
    assert result.links[0].label == "Chapter"


async def test_short_navigation_page_succeeds_while_web_fetch_rejects(monkeypatch):
    link = PageLink("Chapter", "https://example.com/chapter", True, False, None, ())
    page = FetchResult(
        "https://example.com/toc",
        "Contents",
        "short",
        links=(link,),
        text_sufficient=False,
    )
    fetch = AsyncMock(return_value=page)
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)

    links = (await tools.web_links("https://example.com/toc")).model_dump()
    assert links["links"][0]["label"] == "Chapter"
    reading = (await tools.web_fetch("https://example.com/toc")).model_dump()
    assert "too little extractable text" in reading["error"].lower()


async def test_filtering_precedes_pagination_and_continuation_is_versioned(monkeypatch):
    links = tuple(
        [
            PageLink(
                f"external {i}", f"https://outside.example/{i}", False, False, None, ()
            )
            for i in range(60)
        ]
        + [
            PageLink(f"internal {i}", f"https://example.com/{i}", True, False, None, ())
            for i in range(75)
        ]
    )
    page = FetchResult(
        "https://example.com/", "Title", "Readable text. " * 20, links=links
    )
    monkeypatch.setitem(vars(tools), "fetch_page", AsyncMock(return_value=page))

    first = (
        await tools.web_links("https://example.com/", same_origin=True, max_links=50)
    ).model_dump()
    assert len(first["links"]) == 50
    assert first["links"][0]["label"] == "internal 0"
    assert first["total_retained_matching"] == 75
    assert first["next_start_index"] == 50
    assert first["continuation"]["arguments"]["expected_links_hash"] == links_hash(
        links
    )

    second = (await tools.web_links(**first["continuation"]["arguments"])).model_dump()
    assert len(second["links"]) == 25
    assert second["links"][0]["label"] == "internal 50"
    assert second["continuation"] is None


async def test_changed_navigation_rejects_stale_index(monkeypatch):
    first_links = (PageLink("A", "https://example.com/a", True, False, None, ()),)
    second_links = (PageLink("B", "https://example.com/b", True, False, None, ()),)
    fetch = AsyncMock(
        side_effect=[
            FetchResult(
                "https://example.com/",
                "Title",
                "Readable text. " * 20,
                links=first_links,
            ),
            FetchResult(
                "https://example.com/",
                "Title",
                "Readable text. " * 20,
                links=second_links,
            ),
        ]
    )
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    first = (await tools.web_links("https://example.com/")).model_dump()
    stale = (
        await tools.web_links(
            "https://example.com/",
            start_index=1,
            expected_links_hash=first["links_hash"],
        )
    ).model_dump()
    assert stale["error"] == "links_changed"
    assert set(stale) == {"error", "hint"}


async def test_text_and_navigation_versions_are_independent(monkeypatch):
    text = "Readable stable text. " * 20
    first_links = (PageLink("A", "https://example.com/a", True, False, None, ()),)
    second_links = (PageLink("B", "https://example.com/b", True, False, None, ()),)
    fetch = AsyncMock(
        side_effect=[
            FetchResult("https://example.com/", "Title", text, links=first_links),
            FetchResult("https://example.com/", "Title", text, links=first_links),
            FetchResult("https://example.com/", "Title", text, links=second_links),
        ]
    )
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)

    reading = (await tools.web_fetch("https://example.com/")).model_dump()
    first_navigation = (await tools.web_links("https://example.com/")).model_dump()
    second_navigation = (await tools.web_links("https://example.com/")).model_dump()

    assert first_navigation["links_hash"] != second_navigation["links_hash"]
    assert reading["content_hash"] == sha256(text.encode("utf-8")).hexdigest()


async def test_web_fetch_and_web_links_share_one_inflight_page(monkeypatch):
    monkeypatch.setitem(vars(fetcher), "fetch_cache", TTLCache(default_ttl=60))
    monkeypatch.setattr(fetcher, "_fetch_flights", {})
    monkeypatch.setattr(fetcher, "validate_url", AsyncMock(return_value=set()))
    body = (
        b"<html><title>Source</title><body>"
        b"<a href='/chapter'>Chapter</a><p>"
        + b"Readable research material. " * 30
        + b"</p></body></html>"
    )
    download = AsyncMock(
        return_value=(
            "https://example.com/source",
            body,
            httpx.Headers({"content-type": "text/html"}),
        )
    )
    monkeypatch.setattr(fetcher, "_download", download)

    fetched, links = await asyncio.gather(
        tools.web_fetch("https://example.com/source"),
        tools.web_links("https://example.com/source"),
    )
    assert "content" in fetched.model_dump()
    assert links.model_dump()["links"][0]["url"] == "https://example.com/chapter"
    assert download.await_count == 1
