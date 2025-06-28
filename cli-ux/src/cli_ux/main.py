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
from rich.panel import Panel
from rich.prompt import Prompt

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

console = Console()

# Global state for double Ctrl+C detection
last_interrupt_time = 0
DOUBLE_INTERRUPT_THRESHOLD = 0.5

event_bus = EventBus()


def handle_event(event: MessageEvent) -> None:
    """Handle events by displaying them in the console."""
    if isinstance(event, UserMessage):
        # User messages are displayed when typed, not when processed
        pass
    elif isinstance(event, AssistantResponseMessage):
        if event.message:
            console.print(f"● {event.message}")
        # Tool calls will be displayed as separate ToolMessage events
    elif isinstance(event, ToolMessage):
        console.print(f"[green]●[/green] {event.name}(id={event.id})")
        console.print(f"\t{event.content}")


event_bus.subscribe(handle_event)


@click.command()
def chat():
    mcp_client = initialize_mcp_client(Path.cwd())
    agent = Agent(mcp_client=mcp_client)

    console.print(
        Panel.fit(
            "[bold blue]Welcome to TinkerTasker![/bold blue]\n"
            "Your local-first AI assistant.\n\n"
            "[dim]Type 'quit' or 'exit' to end the conversation.[/dim]",
            title="TinkerTasker",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]>[/bold green]")
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
