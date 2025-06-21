import asyncio
from contextlib import suppress
import time

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from cli_ux.types import (
    AssistantResponseMessage,
    EventBus,
    MessageEvent,
    ToolCall,
    ToolMessage,
    TurnContext,
    UserMessage,
)

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
    """Start an interactive chat session with the AI assistant."""
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
            asyncio.run(process_user_message(user_input))
        except KeyboardInterrupt:
            global last_interrupt_time
            current_time = time.time()
            if current_time - last_interrupt_time < DOUBLE_INTERRUPT_THRESHOLD:
                break
            last_interrupt_time = current_time
            continue
        except EOFError:
            break


async def process_user_message(user_input: str) -> None:
    """Process user message using EventBus and TurnContext."""
    with console.status(
        "working... (0.0s ctrl+c to interrupt)", spinner="dots"
    ) as status:
        start_time = time.time()

        async def update_status():
            while True:
                elapsed = time.time() - start_time
                status.update(f"working... ({elapsed:.1f}s ctrl+c to interrupt)")
                await asyncio.sleep(0.05)

        status_task = asyncio.create_task(update_status())

        try:
            async with TurnContext(event_bus) as turn:
                turn.emit_event(UserMessage(content=user_input))
                await asyncio.sleep(1.3)  # Simulate processing delay
                turn.emit_event(
                    AssistantResponseMessage(
                        message="I'll help you with that task.",
                        tool_calls=[
                            ToolCall(
                                name="Read",
                                id="call_1",
                                args="file_path='/path/to/file.py'",
                            )
                        ],
                    )
                )
                await asyncio.sleep(0.7)  # Simulate processing delay
                turn.emit_event(
                    ToolMessage(name="Read", id="call_1", content="File contents read")
                )
        finally:
            status_task.cancel()
            with suppress(asyncio.CancelledError):
                await status_task


if __name__ == "__main__":
    chat()
