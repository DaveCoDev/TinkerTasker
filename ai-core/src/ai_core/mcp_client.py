import argparse
import asyncio
from pathlib import Path

from fastmcp import Client, FastMCP
import mcp.types
from pydantic import FileUrl

from ai_core.agent import Agent
from ai_core.mcp_servers.filesystem.server import mcp as filesystem_server
from ai_core.mcp_servers.web.server import mcp as web_server
from ai_core.schemas import AssistantMessageData, ToolMessageData


def initialize_mcp_client(workspace_path: Path) -> Client:
    composed_mcp = FastMCP()

    # Note: If we want to prefix the tool names with the server name, use the `prefix` argument
    composed_mcp.mount(web_server)
    composed_mcp.mount(filesystem_server)

    client = Client(
        composed_mcp,
        roots=[
            mcp.types.Root(
                uri=FileUrl(f"file://{workspace_path}"),
                name="Working Directory",
            )
        ],
    )
    return client


async def _main(workspace_path: Path):
    """Example usage"""
    client = initialize_mcp_client(workspace_path)
    agent = Agent(mcp_client=client)

    async with client:
        async for event in agent.turn(
            "Can you look what files are in my working directory summarize the first two you see?",
        ):
            if isinstance(event, AssistantMessageData):
                if event.message:
                    print(f"Assistant: {event.message}")
                if event.tool_calls:
                    for tool_call in event.tool_calls:
                        print(f"Tool call: {tool_call.name}({tool_call.args})")
            elif isinstance(event, ToolMessageData):
                print(f"Tool result ({event.name}): {event.content}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path.cwd(),
    )
    args = parser.parse_args()

    asyncio.run(_main(args.work_dir))
