import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


async def test_stdio_protocol():
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_search"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "cluefinch"
            result = await session.list_tools()
            assert {tool.name for tool in result.tools} == {
                "web_search",
                "web_fetch",
                "web_links",
                "research_collect",
            }
            for name, arguments, error in [
                ("web_fetch", {"url": "http://127.0.0.1"}, "blocked_url"),
                ("web_search", {"query": ""}, "query must not be empty"),
                ("web_links", {"url": "http://127.0.0.1"}, "blocked_url"),
                ("research_collect", {}, "nothing to collect"),
            ]:
                response = await session.call_tool(name, arguments)
                assert not response.isError
                assert response.content
                first = response.content[0]
                assert isinstance(first, TextContent)
                assert json.loads(first.text)["error"] == error
