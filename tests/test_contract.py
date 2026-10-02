"""Exercise the contract as a client with no README or AGENTS.md context."""

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import ValidationError

from mcp_search import tools
from mcp_search.fetcher import FetchResult
from mcp_search.models import FetchResponse
from mcp_search.server import mcp


def output_schema(tool: Tool) -> dict[str, Any]:
    schema = tool.outputSchema
    assert isinstance(schema, dict)
    return schema


def response_payload(result: CallToolResult) -> dict[str, Any]:
    assert not result.isError
    assert result.content
    first = result.content[0]
    assert isinstance(first, TextContent)
    payload: dict[str, Any] = json.loads(first.text)
    assert isinstance(payload, dict)
    assert payload == result.structuredContent
    return payload


def definition(schema, name):
    return schema["$defs"][name]


def assert_described_fields(schema, name, fields):
    model = definition(schema, name)
    assert set(model["properties"]) == set(fields)
    assert set(model["required"]) == set(fields)
    assert model["additionalProperties"] is False
    assert all(field.get("description") for field in model["properties"].values())


async def test_discovery_exposes_complete_contracts():
    discovered = {tool.name: tool for tool in await mcp.list_tools()}
    for tool in discovered.values():
        schema = output_schema(tool)
        Draft202012Validator.check_schema(schema)
        assert schema["type"] == "object"
        assert len(schema["anyOf"]) == (
            3 if tool.name in {"web_fetch", "web_links"} else 2
        )
        assert_described_fields(schema, "ToolError", ["error", "hint"])
        assert all(
            field.get("description")
            for field in tool.inputSchema["properties"].values()
        )

    search = discovered["web_search"]
    assert_described_fields(
        search.outputSchema,
        "SearchSuccess",
        ["results", "query_used", "cached", "unresponsive_engines"],
    )
    assert_described_fields(
        search.outputSchema,
        "SearchResult",
        ["title", "url", "snippet", "engine", "source_type"],
    )
    assert "exclude_domains=[" in search.description
    assert "domain=" in search.description
    assert "DO NOT search again" in search.description
    assert "use web_links instead" in search.description
    assert "Results are candidates" in search.description
    assert search.inputSchema["properties"]["max_results"]["default"] == 10

    fetch = discovered["web_fetch"]
    assert_described_fields(
        fetch.outputSchema,
        "FetchSuccess",
        [
            "title",
            "url",
            "content",
            "total_chars",
            "next_start",
            "truncated",
            "cache_hit",
            "source_type",
            "text_truncated",
            "content_hash",
            "continuation",
        ],
    )
    assert "max_chars=500" in fetch.description
    assert "continuation.arguments" in fetch.description
    assert "expand" in fetch.description
    assert "use web_links instead" in fetch.description
    assert "navigation hubs" in fetch.description
    assert "text_truncated" in fetch.description
    assert (
        definition(fetch.outputSchema, "ContentChangedError")["properties"]["error"][
            "const"
        ]
        == "content_changed"
    )
    assert_described_fields(fetch.outputSchema, "FetchAction", ["tool", "arguments"])
    assert_described_fields(
        fetch.outputSchema,
        "WebFetchArguments",
        ["url", "start_offset", "max_chars", "expected_content_hash"],
    )
    assert fetch.inputSchema["properties"]["expected_content_hash"]["default"] is None
    assert fetch.inputSchema["properties"]["max_chars"]["default"] == 10000
    assert (
        f"configured cap {tools.MAX_FETCH_CHARS}"
        in fetch.inputSchema["properties"]["max_chars"]["description"]
    )

    links = discovered["web_links"]
    assert_described_fields(
        links.outputSchema,
        "LinksSuccess",
        [
            "url",
            "links_hash",
            "links",
            "total_retained_matching",
            "next_start_index",
            "links_truncated",
            "cache_hit",
            "continuation",
        ],
    )
    assert_described_fields(
        links.outputSchema,
        "DiscoveredLink",
        ["label", "url", "same_origin", "same_document", "fragment", "rel"],
    )
    assert_described_fields(links.outputSchema, "LinkAction", ["tool", "arguments"])
    assert_described_fields(
        links.outputSchema,
        "WebLinksArguments",
        ["url", "same_origin", "start_index", "max_links", "expected_links_hash"],
    )
    assert (
        definition(links.outputSchema, "LinksChangedError")["properties"]["error"][
            "const"
        ]
        == "links_changed"
    )
    assert links.inputSchema["properties"]["max_links"]["default"] == 50
    assert links.inputSchema["properties"]["same_origin"]["default"] is None
    assert "Filtering happens BEFORE pagination" in links.description
    assert "USE THIS" in links.description
    assert (
        "bridge between web_search discovery and web_fetch reading" in links.description
    )
    assert "NOT a crawler or browser" in links.description
    assert "does not follow them" in links.description
    assert "links_changed" in links.description
    assert "links_truncated" in links.description
    assert "empty links list does not prove" in links.description

    collect = discovered["research_collect"]
    assert_described_fields(
        collect.outputSchema, "CollectSuccess", ["query_variants", "sources", "gaps"]
    )
    assert_described_fields(
        collect.outputSchema,
        "ResearchSource",
        [
            "source_id",
            "title",
            "url",
            "snippet",
            "source_type",
            "excerpts",
            "content_hash",
            "text_truncated",
        ],
    )
    assert_described_fields(
        collect.outputSchema,
        "Excerpt",
        ["text", "start_char", "end_char", "heading", "truncated", "expand"],
    )
    assert "expand.arguments" in collect.description
    assert "does NOT crawl links" in collect.description
    assert "use web_links" in collect.description
    assert "topic alone does not search" in collect.description
    assert "Empty gaps do not prove" in collect.description
    assert collect.inputSchema["properties"]["max_sources"]["default"] == 5


@pytest.mark.parametrize(
    "change",
    [
        {"total_chars": "not an integer"},
        {"unexpected": True},
        {"content_hash": "not a hash"},
        {"error": "mixed success and failure", "hint": ""},
    ],
)
async def test_runtime_and_schema_reject_broken_outputs(monkeypatch, change):
    monkeypatch.setitem(
        vars(tools),
        "fetch_page",
        AsyncMock(
            return_value=FetchResult(
                "https://example.com/", "Title", "Some source text. " * 20
            )
        ),
    )
    payload = (await tools.web_fetch("https://example.com/")).model_dump()
    payload.update(change)
    with pytest.raises(ValidationError):
        FetchResponse.model_validate(payload)
    schema = next(
        output_schema(tool)
        for tool in await mcp.list_tools()
        if tool.name == "web_fetch"
    )
    assert not Draft202012Validator(schema).is_valid(payload)


async def test_preview_continue_expand_over_stdio():
    fixture = Path(__file__).parent / "fixtures" / "contract_server.py"
    params = StdioServerParameters(command=sys.executable, args=[str(fixture)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            instructions = initialized.instructions
            assert isinstance(instructions, str)
            assert "max_chars=500" in instructions
            contracts = {tool.name: tool for tool in (await session.list_tools()).tools}

            async def call(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
                result = await session.call_tool(tool, arguments)
                payload = response_payload(result)
                Draft202012Validator(output_schema(contracts[tool])).validate(payload)
                assert "result" not in payload and "root" not in payload
                return payload

            search = await call(
                "web_search",
                {
                    "query": "asyncio",
                    "domain": "example.com",
                    "exclude_domains": ["ads.example.com"],
                },
            )
            assert (
                search["query_used"] == "asyncio site:example.com -site:ads.example.com"
            )
            assert search["unresponsive_engines"] == ["bing"]
            url = search["results"][0]["url"]
            navigation = await call("web_links", {"url": url, "same_origin": True})
            assert [link["label"] for link in navigation["links"]] == [
                "API reference",
                "Methods",
            ]
            assert navigation["links"][1]["same_document"] is True
            assert navigation["links"][1]["fragment"] == "methods"

            preview = await call("web_fetch", {"url": url, "max_chars": 500})
            assert 0 < len(preview["content"]) <= 500
            assert preview["truncated"] and preview["next_start"] == len(
                preview["content"]
            )
            more = await call(
                "web_fetch",
                {
                    "url": preview["url"],
                    "start_offset": preview["next_start"],
                    "max_chars": 500,
                },
            )
            assert more["next_start"] == preview["next_start"] + len(more["content"])
            assert more["content_hash"] == preview["content_hash"]

            collected = await call(
                "research_collect",
                {"queries": ["asyncio"], "urls": [url, "https://example.com/missing"]},
            )
            assert any("404" in gap for gap in collected["gaps"])
            assert any("bing" in gap for gap in collected["gaps"])
            source = collected["sources"][0]
            excerpt = source["excerpts"][0]
            assert excerpt["heading"] == "Research"
            expanded = await call(
                "web_fetch",
                {
                    "url": source["url"],
                    "start_offset": excerpt["start_char"],
                    "max_chars": 3000,
                },
            )
            assert expanded["content_hash"] == source["content_hash"]
            assert expanded["content"].startswith(excerpt["text"])

            for name, error_arguments in [
                ("web_search", {"query": ""}),
                ("web_fetch", {"url": url, "max_chars": 0}),
                ("web_links", {"url": "http://127.0.0.1"}),
                ("research_collect", {}),
            ]:
                assert set(await call(name, error_arguments)) == {"error", "hint"}


async def test_ready_actions_and_version_guard_over_stdio():
    fixture = Path(__file__).parent / "fixtures" / "contract_server.py"
    params = StdioServerParameters(command=sys.executable, args=[str(fixture)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            contracts = {tool.name: tool for tool in (await session.list_tools()).tools}

            async def call(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
                Draft202012Validator(contracts[tool].inputSchema).validate(arguments)
                result = await session.call_tool(tool, arguments)
                payload = response_payload(result)
                Draft202012Validator(output_schema(contracts[tool])).validate(payload)
                return payload

            first = await call(
                "web_fetch", {"url": "https://example.com/redirect", "max_chars": 500}
            )
            more = await call(**first["continuation"])
            assert more["url"] == "https://example.com/research"
            assert more["content_hash"] == first["content_hash"]
            assert len(more["content"]) <= 500
            assert more["next_start"] == first["next_start"] + len(more["content"])

            collected = await call(
                "research_collect", {"urls": ["https://example.com/redirect"]}
            )
            excerpt = collected["sources"][0]["excerpts"][0]
            expanded = await call(**excerpt["expand"])
            assert expanded["content"].startswith(excerpt["text"])

            changing = await call(
                "web_fetch", {"url": "https://example.com/changing", "max_chars": 500}
            )
            mismatch = await call(**changing["continuation"])
            assert mismatch["error"] == "content_changed"
            assert set(mismatch) == {"error", "hint"}

            changed_source = await call(
                "research_collect", {"urls": ["https://example.com/changing"]}
            )
            mismatch = await call(
                **changed_source["sources"][0]["excerpts"][0]["expand"]
            )
            assert mismatch["error"] == "content_changed"
