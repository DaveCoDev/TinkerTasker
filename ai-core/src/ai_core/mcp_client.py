import argparse
import asyncio
from pathlib import Path

from fastmcp import Client, FastMCP
import mcp.types
from pydantic import FileUrl

from ai_core.mcp_servers.filesystem.server import mcp as filesystem_server
from ai_core.mcp_servers.web.server import mcp as web_server


async def connect_to_servers(workspace_path: Path):
    composed_mcp = FastMCP()

    # Note: If we want to prefix the tool names with the server name, use the `prefix` argument
    composed_mcp.mount(web_server)
    composed_mcp.mount(filesystem_server)

    client = Client(
        composed_mcp,
        roots=[
            mcp.types.Root(
                uri=FileUrl(f"file://{workspace_path.absolute()}"),
                name="Working Directory",
            )
        ],
    )
    async with client:
        tools = await client.list_tools()
        print("Available tools:\n", tools)

        result = await client.call_tool("view", {"path": "."})
        print("Filesystem view:\n", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path.cwd(),
    )
    args = parser.parse_args()

    asyncio.run(connect_to_servers(args.work_dir))
