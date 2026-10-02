from mcp_search.server import mcp


async def test_retrieval_tools_advertise_read_only_open_world_hints():
    discovered = {tool.name: tool for tool in await mcp.list_tools()}

    for name in ("web_search", "web_fetch", "web_links", "research_collect"):
        annotations = discovered[name].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.openWorldHint is True
