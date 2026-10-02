import pytest

from mcp_search.cache import TTLCache, normalize_url
from mcp_search.excerpt import classify_source_type, select_excerpts


def test_cache_expiry_and_lru():
    now = [0]
    cache = TTLCache(default_ttl=10, max_entries=2, clock=lambda: now[0])
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)
    assert cache.get("b") is None
    cache.set("a", 4)
    assert cache.get("c") == 3
    now[0] = 10
    assert cache.get("a") is None


def test_normalization_preserves_query_semantics():
    assert (
        normalize_url("HTTPS://Example.COM:443/x?a=1&b=2#x")
        == "https://example.com/x?a=1&b=2"
    )
    assert normalize_url("https://example.com/?a=1&b=2") != normalize_url(
        "https://example.com/?b=2&a=1"
    )
    assert normalize_url("https://[").startswith("unparsable:")


def test_excerpt_coordinates():
    text = "# Heading\n\n" + "Research with Unicode: наука. " * 40
    excerpts = select_excerpts(text, ["research"], excerpt_chars=100)
    assert excerpts
    for excerpt in excerpts:
        assert excerpt["text"] == text[excerpt["start_char"] : excerpt["end_char"]]
        assert excerpt["heading"] == "Heading"
        assert len(excerpt["text"]) <= 100


def test_ranking_with_two_paragraphs():
    irrelevant = "Apples and oranges grow in orchards. " * 3
    relevant = "Quantum computers use qubits for computation. " * 3
    result = select_excerpts(
        irrelevant + "\n\n" + relevant, ["quantum"], max_excerpts=1
    )
    assert result[0]["text"] == relevant.rstrip()


def test_matching_text_deep_in_long_paragraph():
    text = (
        "Unrelated introduction. " * 100 + "Quantum qubits and research findings. " * 4
    )
    result = select_excerpts(text, ["qubits"], max_excerpts=1)
    assert "qubits" in result[0]["text"]
    assert result[0]["text"] == text[result[0]["start_char"] : result[0]["end_char"]]


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://cdc.gov/", "official"),
        ("https://arxiv.org/abs/x", "academic"),
        ("https://reuters.com/", "news"),
        ("https://medium.com/", "blog"),
        ("https://notreuters.com/", "unknown"),
        ("https://reuters.com.evil.test/", "unknown"),
        ("https://[", "unknown"),
        ("https://pubmed.ncbi.nlm.nih.gov/", "academic"),
    ],
)
def test_category_is_domain_scoped(url, expected):
    assert classify_source_type(url) == expected
