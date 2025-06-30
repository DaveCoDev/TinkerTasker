import ast
import json
from pathlib import Path

from ai_core.schemas import AssistantMessageData, MessageData, ToolMessageData
from rich.console import Console
from rich.panel import Panel

from cli_ux.config import get_config_path
from cli_ux.schemas import AssistantResponseMessage, MessageEvent, ToolCall, ToolMessage


def initial_message(working_dir: Path, console: Console) -> None:
    console.print(
        Panel.fit(
            "[bold #8BC6FC]Welcome to TinkerTasker![/bold #8BC6FC]\n\n"
            f"[dim]Config: {get_config_path()} (restart if changed)[/dim]\n"
            f"[dim]Working Directory: {working_dir} (start from a different dir to change)[/dim]\n\n"
            "[dim]Press CTRL+C twice to quit.[/dim]",
            title="TinkerTasker",
            border_style="#8BC6FC",
        )
    )


def format_tool_arguments(args: str) -> str:
    """Format tool arguments for display."""
    if not args or args.strip() == "{}":
        return "()"

    try:
        # First try ast.literal_eval for Python dict format like {'key': 'value'}
        parsed_args = ast.literal_eval(args)
        if not parsed_args:
            return "()"

        # Format as key=value pairs
        formatted_pairs = []
        for key, value in parsed_args.items():
            if isinstance(value, str):
                formatted_pairs.append(f'{key}="{value}"')
            else:
                formatted_pairs.append(f"{key}={value}")

        return f"({', '.join(formatted_pairs)})"
    except (ValueError, SyntaxError):
        # If ast.literal_eval fails, try JSON format
        try:
            parsed_args = json.loads(args)
            if not parsed_args:
                return "()"

            # Format as key=value pairs
            formatted_pairs = []
            for key, value in parsed_args.items():
                if isinstance(value, str):
                    formatted_pairs.append(f'{key}="{value}"')
                else:
                    formatted_pairs.append(f"{key}={value}")

            return f"({', '.join(formatted_pairs)})"
        except (json.JSONDecodeError, AttributeError):
            # If both fail, return as-is in parentheses
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
