"""Check installed CLI and module entrypoints outside the source checkout."""

import asyncio
import importlib.metadata
import json
import os
import sys
import tempfile
import tomllib
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


class SmokeTestError(RuntimeError):
    """Raised when an installed distribution violates the release contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def _expected_version() -> str:
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project = tomllib.loads(project_file.read_text(encoding="utf-8"))["project"]
    return str(project["version"])


async def main(venv: Path) -> None:
    bindir = venv.resolve() / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    cli = bindir / ("cluefinch.exe" if os.name == "nt" else "cluefinch")
    expected_version = _expected_version()
    _require(
        importlib.metadata.version("cluefinch") == expected_version,
        f"Installed cluefinch version does not match {expected_version}",
    )
    with tempfile.TemporaryDirectory() as cwd:
        for command, args in [(cli, []), (python, ["-m", "mcp_search"])]:
            params = StdioServerParameters(command=str(command), args=args, cwd=cwd)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    _require(
                        initialized.serverInfo.name == "cluefinch",
                        f"Unexpected server name from {command.name}",
                    )
                    listing = await session.list_tools()
                    _require(
                        {t.name for t in listing.tools}
                        == {"web_search", "web_fetch", "web_links", "research_collect"},
                        f"Unexpected tool set from {command.name}",
                    )
                    result = await session.call_tool(
                        "web_fetch", {"url": "http://127.0.0.1"}
                    )
                    _require(
                        not result.isError, "Blocked URL returned an MCP tool error"
                    )
                    _require(bool(result.content), "Blocked URL returned no content")
                    first = result.content[0]
                    if not isinstance(first, TextContent):
                        raise SmokeTestError("Blocked URL result is not text content")
                    payload = json.loads(first.text)
                    _require(
                        payload.get("error") == "blocked_url",
                        "Blocked URL did not return blocked_url",
                    )
                    _require(
                        payload == result.structuredContent,
                        "Text and structured MCP payloads differ",
                    )
            print(f"PASS: {command.name} {' '.join(args)}")


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(Path(sys.argv[1])), timeout=60))
