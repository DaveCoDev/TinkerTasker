import asyncio
from contextlib import suppress
import logging
from pathlib import Path
import time
import warnings

from ai_core.agent import Agent
from ai_core.mcp_client import initialize_mcp_client
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from cli_ux.config import CLIConfig, load_config
from cli_ux.schemas import (
    AssistantResponseMessage,
    EventBus,
    MessageEvent,
    ToolCall,
    ToolMessage,
    TurnContext,
    UserMessage,
)
from cli_ux.ux_utils import (
    convert_data_to_event,
    format_tool_arguments,
    initial_message,
)

config = load_config()

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.CRITICAL)

console = Console(width=120)

event_bus = EventBus(config=config)

# Store tool calls to link with tool messages
_tool_calls_cache: dict[str, ToolCall] = {}


def handle_event(event: MessageEvent, config: CLIConfig) -> None:
    """Handle events (assistant outputs) by displaying them in the console."""
    if isinstance(event, UserMessage):
        console.print()
    elif isinstance(event, AssistantResponseMessage):
        # Cache tool calls for later linking with tool messages
        for tool_call in event.tool_calls:
            _tool_calls_cache[tool_call.id] = tool_call

        if event.message:
            # Use Rich's Table to align dot and content properly
            # Create a table with no borders for layout
            table = Table(show_header=False, show_edge=False, box=None, padding=0)
            table.add_column(width=2, no_wrap=True)  # For the dot
            table.add_column()  # For the content
            table.add_row("●", Markdown(event.message.strip()))
            console.print(table)
            console.print()
    elif isinstance(event, ToolMessage):
        # Get tool arguments from cached tool call
        tool_call = _tool_calls_cache.get(event.id)
        args_display = (
            format_tool_arguments(tool_call.args, config.ux_config.max_arg_value_length)
            if tool_call
            else "()"
        )
        console.print(f"[green]●[/green] {event.name}{args_display}")

        lines = event.content.split("\n")
        max_lines = config.ux_config.number_tool_lines
        # Show all lines if config is -1, otherwise limit to configured amount
        num_lines = len(lines) if max_lines == -1 else min(max_lines, len(lines))

        for i, line in enumerate(lines[:num_lines]):
            prefix = "  ⎿  " if i == 0 else "     "
            console.print(f"{prefix}{line.strip()}")
        console.print()


event_bus.subscribe(handle_event)


@click.command()
def chat():
    working_dir = Path.cwd()

    async def setup_and_chat():
        with console.status(
            "🔧 [bold blue]Initializing TinkerTasker MCP Client...[/bold blue]",
            spinner="dots",
        ):
            mcp_client, mcp_instructions = await initialize_mcp_client(
                working_dir, config.agent_config
            )
        async with mcp_client:
            click.clear()
            with console.status(
                "🔧 [bold blue]Initializing TinkerTasker Tools...[/bold blue]",
                spinner="dots",
            ):
                # This list tools is necessary to ensure the MCP servers are pre-initialized rather than waiting for the first list call.
                await mcp_client.list_tools()
            # These clears and initialization are required because initializing the MCP servers outputs stuff to console from other processes.
            click.clear()

            initial_message(working_dir, console, config.agent_config)
            agent = Agent(
                mcp_client=mcp_client,
                config=config.agent_config,
                working_directory=working_dir,
                mcp_instructions=mcp_instructions,
            )
            while True:
                try:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: Prompt.ask("[bold green]>[/bold green]")
                    )
                    user_input = user_input.strip()
                    if user_input.lower() in ["quit", "exit"]:
                        break
                    if not user_input.strip():
                        continue
                    await process_user_message(user_input, agent)

                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                except Exception as e:
                    console.print(f"\n[red]Error: {e}[/red]")
                    break

    try:
        asyncio.run(setup_and_chat())
    finally:
        console.print("[green]Goodbye![/green]")


async def process_user_message(user_input: str, agent: Agent) -> None:
    """Process user message using EventBus and TurnContext."""
    with console.status(
        "working... (0.0s ctrl+c to interrupt)", spinner="dots"
    ) as status:
        start_time = time.time()

        async def update_status():
            while True:
                elapsed = time.time() - start_time
                status.update(f"working... ({elapsed:.1f}s ctrl+c to interrupt)")
                await asyncio.sleep(0)

        status_task = asyncio.create_task(update_status())

        try:
            async with TurnContext(event_bus) as turn:
                turn.emit_event(UserMessage(content=user_input))
                async for event in agent.turn(user_input):
                    turn.emit_event(convert_data_to_event(event))
                    await asyncio.sleep(0)
        finally:
            status_task.cancel()
            with suppress(asyncio.CancelledError):
                await status_task


if __name__ == "__main__":
    chat()
