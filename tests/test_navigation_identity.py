import socket
from html import escape

import pytest

from mcp_search import security
from mcp_search.navigation import extract_navigation


@pytest.fixture(autouse=True)
def forbid_dns(monkeypatch):
    def unexpected_dns(*args, **kwargs):
        raise AssertionError("Navigation identity must not resolve DNS")

    monkeypatch.setattr(socket, "getaddrinfo", unexpected_dns)
    monkeypatch.setattr(security, "_resolve_host", unexpected_dns)


@pytest.mark.parametrize("href", ["/café#x", "/caf%C3%A9#x"])
def test_unicode_and_encoded_paths_match_final_document(href):
    result = extract_navigation(
        f'<a href="{href}">X</a>', "https://example.com/caf%C3%A9"
    )
    assert result.links[0].url == "https://example.com/caf%C3%A9#x"
    assert result.links[0].same_document


def test_equivalent_links_deduplicate_but_distinct_fragments_remain():
    result = extract_navigation(
        '<a href="/café#x" rel="next">First</a>'
        '<a href="/caf%C3%A9#x" rel="help">Duplicate</a>'
        '<a href="/café#y">Second</a>',
        "https://example.com/caf%C3%A9",
    )
    assert [link.url for link in result.links] == [
        "https://example.com/caf%C3%A9#x",
        "https://example.com/caf%C3%A9#y",
    ]
    assert all(link.same_document for link in result.links)
    assert result.links[0].label == "First"
    assert result.links[0].rel == ("next", "help")


def test_unicode_query_and_fragment_use_httpx_serialization():
    result = extract_navigation(
        '<a href="/x?q=café#café">Unicode</a>'
        '<a href="/x?q=caf%C3%A9#caf%C3%A9">Encoded</a>',
        "https://example.com/x?q=caf%C3%A9",
    )
    assert len(result.links) == 1
    assert result.links[0].url == "https://example.com/x?q=caf%C3%A9#caf%C3%A9"
    assert result.links[0].fragment == "caf%C3%A9"
    assert result.links[0].same_document


def test_query_order_is_not_canonicalized():
    result = extract_navigation(
        '<a href="/x?b=2&amp;a=1">First</a><a href="/x?a=1&amp;b=2">Second</a>',
        "https://example.com/x?b=2&a=1",
    )
    assert [link.url for link in result.links] == [
        "https://example.com/x?b=2&a=1",
        "https://example.com/x?a=1&b=2",
    ]
    assert [link.same_document for link in result.links] == [True, False]


@pytest.mark.parametrize("character", list(":/?#[]@!$&'()*+,;="))
@pytest.mark.parametrize("component", ["path", "query", "fragment"])
def test_encoded_reserved_characters_are_not_decoded(character, component):
    encoded = f"%{ord(character):02X}"
    template = {"path": "/a{}b", "query": "/x?q=a{}b", "fragment": "/x#a{}b"}[component]
    href = template.format(encoded)
    literal = template.format(character)
    result = extract_navigation(
        f'<a href="{escape(href, quote=True)}">Encoded</a>'
        f'<a href="{escape(literal, quote=True)}">Literal</a>',
        "https://example.com/",
    )
    assert len(result.links) == 2
    assert result.links[0].url == "https://example.com" + href
    assert result.links[0].url != result.links[1].url


@pytest.mark.parametrize("base", ["", '<base href="/café/">'])
def test_relative_links_and_base_keep_resolution_semantics(base):
    result = extract_navigation(
        base + '<a href="chapter#x">Relative</a>'
        '<a href="/caf%C3%A9/chapter#x">Absolute</a>'
        '<a href="../appendix">Parent</a>',
        "https://example.com/caf%C3%A9/index",
    )
    assert [link.url for link in result.links] == [
        "https://example.com/caf%C3%A9/chapter#x",
        "https://example.com/appendix",
    ]
