from fastmcp import Client

from ai_core.mcp_servers.web.server import mcp


async def test_fetch():
    async with Client(mcp) as client:
        result = await client.call_tool("fetch", {"url": "https://example.com/"})
        print(result)
