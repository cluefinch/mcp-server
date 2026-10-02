"""Ready actions must be executable unchanged, safe across text versions and optional."""

from hashlib import sha256
from unittest.mock import AsyncMock

import httpx
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from mcp_search import fetcher, tools
from mcp_search.cache import TTLCache
from mcp_search.fetcher import FetchResult
from mcp_search.models import ContentChangedError, FetchAction, ToolError
from mcp_search.server import mcp

URL = "https://8.8.8.8/source"
FINAL_URL = "https://8.8.8.8/final"
TEXT = "\n\n".join("Я🧭🙂é" * 13 for _ in range(6))


async def execute(action):
    assert action["tool"] == "web_fetch"
    return (await tools.web_fetch(**action["arguments"])).model_dump()


async def test_copy_continuation_reconstructs_unicode_text(monkeypatch):
    fetch = AsyncMock(return_value=FetchResult(FINAL_URL, "Title", TEXT))
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    first = (await tools.web_fetch(URL, max_chars=80)).model_dump()
    assert first["next_start"] == 52  # Paragraph boundary, not the requested 80.
    assert len(first["content"].encode("utf-8")) != first["next_start"]
    assert len(first["content"].encode("utf-16-le")) // 2 != first["next_start"]
    parts = [first["content"]]
    current = first
    schema = next(
        tool.inputSchema for tool in await mcp.list_tools() if tool.name == "web_fetch"
    )
    while current["continuation"] is not None:
        action = current["continuation"]
        Draft202012Validator(schema).validate(action["arguments"])
        assert action["arguments"] == {
            "url": FINAL_URL,
            "start_offset": current["next_start"],
            "max_chars": 80,
            "expected_content_hash": first["content_hash"],
        }
        current = await execute(action)
        parts.append(current["content"])
    assert "".join(parts) == TEXT
    assert current["next_start"] is None and current["truncated"] is False
    assert fetch.await_count == len(parts)  # No extra fetches to build actions.


async def test_effective_budget_is_preserved_not_returned_length(monkeypatch):
    monkeypatch.setattr(tools, "MAX_FETCH_CHARS", 73)
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(return_value=FetchResult(URL, "Title", TEXT)),
    )
    first = (await tools.web_fetch(URL, max_chars=500)).model_dump()
    assert len(first["content"]) == 52
    assert first["continuation"]["arguments"]["max_chars"] == 73
    assert (await execute(first["continuation"]))["continuation"]["arguments"][
        "max_chars"
    ] == 73


@pytest.mark.parametrize("offset", [0, len(TEXT), len(TEXT) + 100])
async def test_retained_end_and_dropped_tail_are_independent(monkeypatch, offset):
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(return_value=FetchResult(URL, "Title", TEXT, text_truncated=True)),
    )
    result = (
        await tools.web_fetch(URL, start_offset=offset, max_chars=len(TEXT))
    ).model_dump()
    assert result["continuation"] is None
    assert result["next_start"] is None and result["truncated"] is False
    assert result["text_truncated"] is True
    assert result["content"] == TEXT[offset:]


@pytest.mark.parametrize("action_name", ["continuation", "expand"])
@pytest.mark.parametrize("cache_hit", [False, True])
async def test_changed_text_rejected_before_slicing(
    monkeypatch, action_name, cache_hit
):
    fetch = AsyncMock(
        side_effect=[
            FetchResult(URL, "Title", TEXT),
            FetchResult(URL, "Title", TEXT[:-1] + "X", cache_hit=cache_hit),
        ]
    )
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    if action_name == "continuation":
        action = (await tools.web_fetch(URL, max_chars=80)).model_dump()["continuation"]
    else:
        source = (await tools.research_collect(urls=[URL])).model_dump()["sources"][0]
        action = source["excerpts"][0]["expand"]

    def forbidden_slice(*_args):
        pytest.fail("stale coordinates reached the slicer")

    monkeypatch.setattr(tools, "_cut_at_paragraph", forbidden_slice)
    result = await tools.web_fetch(**action["arguments"])
    assert isinstance(result.root, ContentChangedError)
    assert result.root.error == "content_changed"
    assert set(result.model_dump()) == {"error", "hint"}
    assert fetch.await_count == 2  # No automatic retry after a version mismatch.


@pytest.mark.parametrize("changed", [False, True])
async def test_expired_cache_rechecks_retained_text_not_cache_status(
    monkeypatch, changed
):
    clock = [0.0]
    monkeypatch.setitem(
        vars(fetcher), "fetch_cache", TTLCache(default_ttl=10, clock=lambda: clock[0])
    )
    old = (
        b"<html><title>Source</title><body><p>"
        + b"Evidence for reading documents. " * 80
        + b"</p></body></html>"
    )
    new = old.replace(b"Evidence", b"New data") if changed else old
    download = AsyncMock(
        side_effect=[
            (FINAL_URL, old, httpx.Headers({"content-type": "text/html"})),
            (FINAL_URL, new, httpx.Headers({"content-type": "text/html"})),
        ]
    )
    monkeypatch.setattr(fetcher, "_download", download)
    first = (await tools.web_fetch(URL, max_chars=100)).model_dump()
    action = first["continuation"]
    assert action["arguments"]["url"] == FINAL_URL
    cached = await execute(action)
    assert cached["cache_hit"] is True
    clock[0] = 11
    fresh = await execute(action)
    if changed:
        assert fresh["error"] == "content_changed"
    else:
        assert fresh["content_hash"] == first["content_hash"]
        assert fresh["cache_hit"] is False
    assert download.await_count == 2


@pytest.mark.parametrize("budget,cap", [(3000, 20000), (10000, 800), (80, 1000)])
async def test_expand_is_self_contained_and_bounded(monkeypatch, budget, cap):
    monkeypatch.setattr(tools, "EXPAND_CHARS", budget)
    monkeypatch.setattr(tools, "MAX_FETCH_CHARS", cap)
    fetch = AsyncMock(return_value=FetchResult(FINAL_URL, "Title", TEXT))
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    source = (await tools.research_collect(urls=[URL])).model_dump()["sources"][0]
    assert fetch.await_count == 1
    assert source["excerpts"]
    for excerpt in source["excerpts"]:
        action = excerpt["expand"]
        assert action["arguments"] == {
            "url": FINAL_URL,
            "start_offset": excerpt["start_char"],
            "max_chars": min(budget, cap),
            "expected_content_hash": source["content_hash"],
        }
        expanded = await execute(action)
        assert expanded["content_hash"] == source["content_hash"]
        assert expanded["content"].startswith(excerpt["text"])
        assert len(expanded["content"]) <= min(budget, cap)
    assert fetch.await_count == 1 + len(source["excerpts"])


async def test_manual_calls_remain_unguarded_and_guard_is_optional(monkeypatch):
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(return_value=FetchResult(URL, "Title", TEXT)),
    )
    manual = (await tools.web_fetch(URL, 52, 80)).model_dump()
    guarded = (await tools.web_fetch(URL, 52, 80, manual["content_hash"])).model_dump()
    assert guarded == manual
    assert (await tools.web_fetch(URL, 52, 80, None)).model_dump() == manual


@pytest.mark.parametrize("invalid", ["", "A" * 64, "0" * 63, "g" * 64])
async def test_invalid_hash_does_not_fetch(monkeypatch, invalid):
    fetch = AsyncMock()
    monkeypatch.setitem(vars(tools), "fetch_page", fetch)
    response = await tools.web_fetch(URL, expected_content_hash=invalid)
    error = response.root
    assert isinstance(error, ToolError)
    assert "expected_content_hash" in error.error
    fetch.assert_not_awaited()


async def test_action_execution_still_validates_url():
    result = await tools.web_fetch(
        url="http://127.0.0.1/",
        start_offset=0,
        max_chars=80,
        expected_content_hash=sha256(TEXT.encode()).hexdigest(),
    )
    error = result.root
    assert isinstance(error, ToolError)
    assert error.error == "blocked_url"


@pytest.mark.parametrize(
    "change",
    [
        {"tool": "bash"},
        {"arguments": {}},
        {
            "arguments": {
                "url": URL,
                "start_offset": -1,
                "max_chars": 80,
                "expected_content_hash": "0" * 64,
            }
        },
    ],
)
def test_action_contract_rejects_arbitrary_or_incomplete_calls(change):
    action = {
        "tool": "web_fetch",
        "arguments": {
            "url": URL,
            "start_offset": 0,
            "max_chars": 80,
            "expected_content_hash": "0" * 64,
        },
    }
    action.update(change)
    with pytest.raises(ValidationError):
        FetchAction.model_validate(action)
