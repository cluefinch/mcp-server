"""Reusable MCP stdio-client harness for phase gates.

Usage as a script:
    uv run python scripts/mcp_client_test.py <tool_name> [json_args]
Prints {"tools": [...], "isError": bool, "result": ...} and exits 1 on isError.

Importable from gate scripts (same directory):
    from mcp_client_test import call_tool, call_tools
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_search"],
        env={
            key: value
            for key, value in os.environ.items()
            if key.startswith("MCP_SEARCH_")
        },
    )


async def _call(session: ClientSession, name: str, arguments: dict) -> object:
    result = await session.call_tool(name, arguments)
    if result.isError:
        text = (
            " ".join(
                item.text for item in result.content if isinstance(item, TextContent)
            )
            or "tool error"
        )
        raise RuntimeError(f"{name} returned isError: {text}")
    payload: object = None
    if result.content:
        first = result.content[0]
        if not isinstance(first, TextContent):
            raise RuntimeError(f"{name} returned non-text content")
        raw = first.text
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = raw
    return payload


async def call_tool(
    name: str, arguments: dict | None = None
) -> tuple[list[str], object]:
    """One session, one call. Returns (tool_names, payload)."""
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            payload = await _call(session, name, arguments or {})
    return names, payload


async def call_tools(calls: list[tuple[str, dict]]) -> tuple[list[str], list[object]]:
    """One session, multiple calls (needed to test in-process caches).

    Returns (tool_names, [payload per call]).
    """
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            payloads = [await _call(session, n, a) for n, a in calls]
    return names, payloads


async def _main() -> int:
    if len(sys.argv) < 2:
        print(__doc__ or "")
        return 2
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    names, payload = await call_tool(tool, args)
    print(
        json.dumps(
            {"tools": names, "isError": False, "result": payload},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
