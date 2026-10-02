"""Regression coverage for URL identity, inactive HTML and text retention."""

import socket
from unittest.mock import AsyncMock

import httpx
import pytest

from mcp_search import fetcher, navigation, security, tools
from mcp_search.navigation import extract_navigation


@pytest.mark.parametrize("final_host", ["faß.de", "xn--fa-hia.de"])
def test_idna_matches_transport_for_links_and_base(monkeypatch, final_host):
    def no_dns(*_args, **_kwargs):
        raise AssertionError("Link discovery must not resolve destinations")

    monkeypatch.setattr(socket, "getaddrinfo", no_dns)
    monkeypatch.setattr(security, "_resolve_host", no_dns)
    html = """<base href="https://faß.de/guide/">
    <a href="chapter#one">Relative</a>
    <a href="https://faß.de/guide/chapter#one">Unicode duplicate</a>
    <a href="https://xn--fa-hia.de/guide/chapter#one">ASCII duplicate</a>
    <a href="https://faß.de/report#section">Section</a>
    <a href="https://fass.de/report">Different host</a>"""
    result = extract_navigation(html, f"https://{final_host}/report")
    assert len(result.links) == 3
    relative, section, other = result.links
    assert relative.url == "https://xn--fa-hia.de/guide/chapter#one"
    assert relative.same_origin and not relative.same_document
    assert section.same_origin and section.same_document
    assert not other.same_origin and not other.same_document
    assert httpx.URL(relative.url).raw_host == httpx.URL("https://faß.de/").raw_host
    assert security.normalize_hostname("faß.de") == "xn--fa-hia.de"


def test_ipv6_origin_uses_shared_hostname_normalization():
    result = extract_navigation(
        '<a href="https://[2606:4700:4700::1111]:443/report#x">X</a>',
        "https://[2606:4700:4700::1111]/report",
    )
    assert result.links[0].same_origin and result.links[0].same_document


@pytest.mark.parametrize("tag", ["script", "style", "noscript", "template"])
def test_inactive_subtrees_do_not_consume_scan_budget(monkeypatch, tag):
    monkeypatch.setattr(navigation, "MAX_LINK_ELEMENTS_SCANNED", 1)
    result = extract_navigation(
        f'<{tag}><span><a href="/hidden">Hidden</a></span></{tag}>'
        '<a href="/real">Real</a>',
        "https://example.com/",
    )
    assert [link.url for link in result.links] == ["https://example.com/real"]
    assert not result.links_truncated


@pytest.mark.parametrize("tag", ["script", "style", "noscript", "template"])
def test_label_excludes_comments_and_nested_inactive_content(tag):
    result = extract_navigation(
        '<a href="/x" aria-label="Actual"><!-- hidden instruction -->'
        f"<{tag}><span>Inactive label</span></{tag}></a>",
        "https://example.com/",
    )
    assert result.links[0].label == "Actual"
    assert not result.links_truncated


@pytest.mark.parametrize("long_text", [False, True])
async def test_suitability_survives_retention_and_cache(monkeypatch, long_text):
    text = "Readable research material. " * 20 if long_text else "Tiny"
    html = f'<p>{text}</p><a href="/chapter">Next</a>'.encode()
    monkeypatch.setattr(fetcher, "MAX_TEXT_CHARS", 10)
    monkeypatch.setattr(fetcher, "validate_url", AsyncMock(return_value=set()))
    monkeypatch.setattr(security, "validate_url", AsyncMock(return_value=set()))
    download = AsyncMock(
        return_value=(
            "https://example.com/report",
            html,
            httpx.Headers({"content-type": "text/html"}),
        )
    )
    monkeypatch.setattr(fetcher, "_download", download)
    url = "https://example.com/report"

    fresh = await fetcher.fetch_page(url)
    cached = await fetcher.fetch_page(url)
    assert fresh.text_sufficient is long_text
    assert cached.text_sufficient is long_text
    assert not fresh.cache_hit and cached.cache_hit
    assert len(cached.text) <= 10

    read = (await tools.web_fetch(url)).model_dump()
    collected = (await tools.research_collect(urls=[url])).model_dump()
    links = (await tools.web_links(url)).model_dump()
    if long_text:
        assert read["content"] == fresh.text
        assert read["text_truncated"] is True
        assert len(collected["sources"]) == 1
    else:
        assert "too little extractable text" in read["error"].lower()
        assert not collected["sources"]
        assert any("too little extractable text" in gap for gap in collected["gaps"])
    assert links["links"][0]["url"] == "https://example.com/chapter"
    download.assert_awaited_once()
