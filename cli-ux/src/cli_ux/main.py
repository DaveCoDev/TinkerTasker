import asyncio
from contextlib import suppress
import logging
from pathlib import Path
import time
import warnings

from ai_core.agent import Agent
from ai_core.mcp_client import initialize_mcp_client
from ai_core.schemas import AssistantMessageData, MessageData, ToolMessageData
import click
from fastmcp import Client
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from cli_ux.config import get_config_path, load_config
from cli_ux.schemas import (
    AssistantResponseMessage,
    EventBus,
    MessageEvent,
    ToolCall,
    ToolMessage,
    TurnContext,
    UserMessage,
)

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.CRITICAL)

console = Console(width=120)

# Global state for double Ctrl+C detection
last_interrupt_time = 0
DOUBLE_INTERRUPT_THRESHOLD = 0.5

event_bus = EventBus()


def handle_event(event: MessageEvent) -> None:
    """Handle events by displaying them in the console."""
    if isinstance(event, UserMessage):
        console.print()
    elif isinstance(event, AssistantResponseMessage):
        if event.message:
            # Use Rich's Table to align dot and content properly
            # Create a table with no borders for layout
            table = Table(show_header=False, show_edge=False, box=None, padding=0)
            table.add_column(width=2, no_wrap=True)  # For the dot
            table.add_column()  # For the content
            table.add_row("●", Markdown(event.message.strip()))
            console.print(table)
            console.print()
    # Tool calls will be displayed as separate ToolMessage events
    elif isinstance(event, ToolMessage):
        # Get first line of content only
        first_line = event.content.split("\n")[0].strip()
        console.print(f"[green]●[/green] {event.name}(.)")
        console.print(f"  ⎿  {first_line}")
        console.print()


event_bus.subscribe(handle_event)


def initial_message(working_dir: Path) -> None:
    console.print(
        Panel.fit(
            "[bold #8BC6FC]Welcome to TinkerTasker![/bold #8BC6FC]\n\n"
            f"[dim]Config: {get_config_path()}[/dim]\n"
            f"[dim]Working Directory: {working_dir}[/dim]\n\n"
            "[dim]Press CTRL+C twice to quit.[/dim]",
            title="TinkerTasker",
            border_style="#8BC6FC",
        )
    )


@click.command()
def chat():
    config = load_config()
    working_dir = Path.cwd()
    mcp_client = initialize_mcp_client(working_dir)
    agent = Agent(mcp_client=mcp_client, config=config.agent_config)

    initial_message(working_dir)

    while True:
        try:
            user_input = Prompt.ask("[bold green]>[/bold green]")
            user_input = user_input.strip()
            if user_input.lower() in ["quit", "exit"]:
                break
            if not user_input.strip():
                continue
            asyncio.run(process_user_message(user_input, mcp_client, agent))
        except KeyboardInterrupt:
            global last_interrupt_time
            current_time = time.time()
            if current_time - last_interrupt_time < DOUBLE_INTERRUPT_THRESHOLD:
                break
            last_interrupt_time = current_time
            continue
        except EOFError:
            break


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


async def process_user_message(
    user_input: str, mcp_client: Client, agent: Agent
) -> None:
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
                async with mcp_client:
                    async for event in agent.turn(user_input):
                        turn.emit_event(convert_data_to_event(event))
                        await asyncio.sleep(0)
        finally:
            status_task.cancel()
            with suppress(asyncio.CancelledError):
                await status_task


if __name__ == "__main__":
    chat()
