"""Measure contract/response JSON size with deterministic, network-free fixtures.

This measures characters and UTF-8 bytes, not model-dependent token counts.
Run with the same environment before and after a contract change.
"""

import asyncio
import json
from unittest.mock import patch

from mcp_search import __version__, tools
from mcp_search.fetcher import FetchResult
from mcp_search.server import mcp

TEXT = "\n\n".join(
    f"# Section {i}\n\n" + "Evidence about document navigation. Context 🧭. " * 20
    for i in range(4)
)


def size(value: object) -> dict[str, int]:
    serialized = json.dumps(value, ensure_ascii=False, indent=2)
    return {
        "characters": len(serialized),
        "utf8_bytes": len(serialized.encode("utf-8")),
    }


async def measure() -> dict[str, object]:
    async def fetch(url: str) -> FetchResult:
        return FetchResult(url, "Navigation fixture", TEXT)

    result: dict[str, object] = {
        "version": __version__,
        "serialization": "JSON, ensure_ascii=False, indent=2",
        "tools": {
            tool.name: {
                "output_schema": size(tool.outputSchema),
                "input_schema": size(tool.inputSchema),
                "description": size(tool.description),
            }
            for tool in await mcp.list_tools()
        },
    }
    with patch.dict(vars(tools), {"fetch_page": fetch}):
        result["fetch_500"] = size(
            (
                await tools.web_fetch("https://example.org/source/0", max_chars=500)
            ).model_dump()
        )
        collections = {}
        for count in sorted({min(5, tools.MAX_SOURCES_CAP), tools.MAX_SOURCES_CAP}):
            payload = (
                await tools.research_collect(
                    urls=[f"https://example.org/source/{i}" for i in range(count)],
                    topic="evidence",
                    max_sources=count,
                )
            ).model_dump()
            collections[str(count)] = {
                "sources": len(payload["sources"]),
                "excerpts": sum(
                    len(source["excerpts"]) for source in payload["sources"]
                ),
                **size(payload),
            }
        result["collections"] = collections
    return result


if __name__ == "__main__":
    print(json.dumps(asyncio.run(measure()), ensure_ascii=False, indent=2))
