from fastmcp import Client
from mcp.types import TextContent

from ai_core.mcp_servers.web.server import mcp


async def test_search():
    """Test the search tool."""
    async with Client(mcp) as client:
        result = await client.call_tool("search", {"query": "Python MCP"})
        assert result == [TextContent(type="text", text="Search not implemented yet.")]
