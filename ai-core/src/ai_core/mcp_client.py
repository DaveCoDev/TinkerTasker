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


async def initialize_mcp_client(
    workspace_path: Path, config: AgentConfig
) -> tuple[Client, str]:
    instructions_parts = []

    # Collect instructions from enabled native servers
    available_native_servers = {
        "filesystem": filesystem_server,
        "web": web_server,
    }
    enabled_native_servers = []
    for server_name in set(config.native_mcp_servers):
        if server_name in available_native_servers:
            server = available_native_servers[server_name]
            enabled_native_servers.append(server)
            if hasattr(server, "instructions") and server.instructions:
                display_name = getattr(server, "name", server_name.title())
                instructions_parts.append(
                    f"### {display_name} Server\n{server.instructions}"
                )

    # Process all external MCP servers from config first to get their info
    external_servers = []
    for server_config in config.mcp_servers:
        mcp_config = {
            "mcpServers": {
                server_config.identifier: {
                    "command": server_config.command,
                    "args": server_config.args,
                }
            }
        }

        # Connect to get server info
        client_for_info = Client(mcp_config)
        try:
            async with client_for_info:
                await client_for_info.ping()
                result = client_for_info.initialize_result
                server_name = server_config.identifier
                if result and result.serverInfo:
                    server_name = result.serverInfo.name
                    server_instructions = result.instructions or ""
                    if server_instructions:
                        instructions_parts.append(
                            f"## {server_name} Server\n{server_instructions}"
                        )
                external_servers.append(
                    {
                        "config": mcp_config,
                        "name": server_name,
                        "prefix": server_config.prefix,
                    }
                )
        except Exception as e:
            print(
                f"Warning: Failed to get info from {server_config.identifier}: {e}.\nServer not being added."
            )

    combined_instructions = (
        "\n\n".join(instructions_parts) if instructions_parts else ""
    )

    composed_mcp = FastMCP()

    # Mount only the enabled native servers
    for server in enabled_native_servers:
        composed_mcp.mount(server)

    # Mount external servers
    for server_info in external_servers:
        client_for_mount = Client(server_info["config"])
        proxy = FastMCP.as_proxy(client_for_mount, name=server_info["name"])
        composed_mcp.mount(proxy, prefix=server_info["prefix"])

    client = Client(
        composed_mcp,
        roots=[
            mcp.types.Root(
                uri=FileUrl(f"file://{workspace_path}"),
                name="Working Directory",
            )
        ],
    )

    # Only add the native servers header if there are enabled native servers
    if enabled_native_servers:
        initial_string = "## Native MCP Servers\nThese servers are provided by default by TinkerTasker.\n\n"
        combined_instructions = initial_string + combined_instructions

    return client, combined_instructions


async def _main(workspace_path: Path):
    """Example usage"""
    config = AgentConfig()
    client, mcp_instructions = await initialize_mcp_client(workspace_path, config)
    async with client:
        agent = Agent(
            mcp_client=client,
            config=config,
            working_directory=workspace_path,
            mcp_instructions=mcp_instructions,
        )
        async for event in agent.turn(
            "Can you look what files are in my working directory summarize the first two you see? Then use context7 to search for the numpy documentation",
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
