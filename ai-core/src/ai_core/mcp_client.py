import argparse
import asyncio
from pathlib import Path

from fastmcp import Client, FastMCP
import mcp.types
from pydantic import FileUrl

from ai_core.agent import Agent
from ai_core.config import AgentConfig
from ai_core.mcp_servers.filesystem.server import mcp as filesystem_server
from ai_core.mcp_servers.web.server import mcp as web_server
from ai_core.schemas import AssistantMessageData, ToolMessageData


def initialize_mcp_client(workspace_path: Path) -> Client:
    instructions_parts = []
    for server in [filesystem_server, web_server]:
        if hasattr(server, "instructions") and server.instructions:
            server_name = getattr(server, "name", "Unknown")
            instructions_parts.append(
                f"### {server_name} Server\n{server.instructions}"
            )
    combined_instructions = (
        "\n\n".join(instructions_parts) if instructions_parts else None
    )

    composed_mcp = FastMCP(
        name="Native MCP Servers\nThese servers are provided by default by TinkerTasker.",
        instructions=combined_instructions,
    )

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


async def initialize_mcp_servers(
    client: Client, result: mcp.types.InitializeResult
) -> str:
    await client.ping()
    result = client.initialize_result

    mcp_instructions = "\n".join(
        ["## " + result.serverInfo.name, "", result.instructions or ""]
    )
    return mcp_instructions.strip()


async def _main(workspace_path: Path):
    """Example usage"""
    client = initialize_mcp_client(workspace_path)
    async with client:
        mcp_instructions = await initialize_mcp_servers(
            client, client.initialize_result
        )
        agent = Agent(
            mcp_client=client,
            config=AgentConfig(),
            working_directory=workspace_path,
            mcp_instructions=mcp_instructions,
        )
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
