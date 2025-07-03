import ast
import json
from pathlib import Path

from ai_core.config import AgentConfig
from ai_core.schemas import AssistantMessageData, MessageData, ToolMessageData
from rich.console import Console
from rich.panel import Panel

from cli_ux.config import get_config_path
from cli_ux.schemas import AssistantResponseMessage, MessageEvent, ToolCall, ToolMessage


def initial_message(
    working_dir: Path, console: Console, agent_config: AgentConfig
) -> None:
    # Get a list of enabled MCP servers to print
    enabled_servers = []
    enabled_servers.extend(sorted(agent_config.native_mcp_servers))
    enabled_servers.extend([server.identifier for server in agent_config.mcp_servers])
    mcp_info = (
        f"[dim]Enabled MCP Servers: {', '.join(enabled_servers)}[/dim]"
        if enabled_servers
        else "[dim]No MCP Servers enabled[/dim]"
    )

    console.print(
        Panel.fit(
            "[bold #8BC6FC]Welcome to TinkerTasker![/bold #8BC6FC]\n\n"
            f"[dim]Config: {get_config_path()} (restart if changed)[/dim]\n"
            f"[dim]Working Directory: {working_dir} (start from a different dir to change)[/dim]\n"
            f"[dim]LiteLLM Model Name: {agent_config.llm_config.model_name}[/dim]\n"
            f"{mcp_info}\n\n"
            "[dim]Press CTRL+C twice to quit.[/dim]",
            title="TinkerTasker",
            border_style="#8BC6FC",
        )
    )


def format_tool_arguments(args: str, max_arg_value_length: int = 50) -> str:
    """Format tool arguments for display."""
    if not args or args.strip() == "{}":
        return "()"

    def format_parsed_args(parsed_args: dict) -> str:
        """Helper function to format parsed arguments."""
        if not parsed_args:
            return "()"

        formatted_pairs = []
        for key, value in parsed_args.items():
            # Convert to string and normalize whitespace
            value_str = str(value)
            cleaned_value = " ".join(value_str.split())

            # Truncate if needed
            truncated_value = (
                cleaned_value[:max_arg_value_length] + "..."
                if len(cleaned_value) > max_arg_value_length
                else cleaned_value
            )

            # Add quotes for string values
            if isinstance(value, str):
                formatted_pairs.append(f'{key}="{truncated_value}"')
            else:
                formatted_pairs.append(f"{key}={truncated_value}")

        return f"({', '.join(formatted_pairs)})"

    # Try parsing with ast.literal_eval first, then JSON
    for parser in [ast.literal_eval, json.loads]:
        try:
            parsed_args = parser(args)
            return format_parsed_args(parsed_args)
        except (ValueError, SyntaxError, json.JSONDecodeError, AttributeError):
            continue

    # If both parsers fail, return as-is
    return f"({args})" if args else "()"


def convert_data_to_event(data: MessageData) -> MessageEvent:
    """Convert MessageData schemas from the ai core Agent to the cli's MessageEvent schemas."""
    if isinstance(data, AssistantMessageData):
        tool_calls = [
            ToolCall(name=tc.name, id=tc.id, args=str(tc.args))
            for tc in data.tool_calls
        ]
        return AssistantResponseMessage(message=data.message, tool_calls=tool_calls)
    elif isinstance(data, ToolMessageData):
        return ToolMessage(name=data.name, id=data.id, content=data.content)
    else:
        return AssistantResponseMessage(
            message="Something went wrong, no data received from the agent"
        )
