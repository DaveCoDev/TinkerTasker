import asyncio
import time

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from cli_ux.types import AssistantResponseMessage, ToolCall, ToolMessage

console = Console()

# Global state for double Ctrl+C detection
last_interrupt_time = 0
DOUBLE_INTERRUPT_THRESHOLD = 0.5


def get_ai_response(user_message: str) -> AssistantResponseMessage:
    """Mock AI response with hardcoded examples."""
    if "tool" in user_message.lower():
        return AssistantResponseMessage(
            message="I'll help you with that task.",
            tool_calls=[
                ToolCall(name="Read", id="call_1", args="file_path='/path/to/file.py'"),
            ],
        )
    else:
        return AssistantResponseMessage(
            message="Hello I am an assistant. How can I help you today?"
        )


def get_tool_output(tool_call: ToolCall) -> ToolMessage:
    """Mock tool execution - returns hardcoded output."""
    if tool_call.name == "Read":
        return ToolMessage(
            name=tool_call.name, id=tool_call.id, content="File contents here..."
        )
    elif tool_call.name == "Edit":
        return ToolMessage(
            name=tool_call.name, id=tool_call.id, content="File edited successfully"
        )
    else:
        return ToolMessage(
            name=tool_call.name, id=tool_call.id, content="Tool executed successfully"
        )


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
    """Process user message with live progress indicator and formatted output."""
    response_duration = 1.3
    start_time = time.time()

    try:
        # Initial thinking/processing
        with console.status(
            "working... (0.0s ctrl+c to interrupt)", spinner="dots"
        ) as status:
            while time.time() - start_time < response_duration:
                elapsed = time.time() - start_time
                status.update(f"working... ({elapsed:.1f}s ctrl+c to interrupt)")
                await asyncio.sleep(0.1)

        # Get and display the initial response
        ai_response = get_ai_response(user_input)

        if ai_response.message:
            console.print(f"● {ai_response.message}")

        # Process tool calls sequentially
        if ai_response.tool_calls:
            for tool_call in ai_response.tool_calls:
                # Display the tool call
                console.print(f"[green]●[/green] {tool_call.name}({tool_call.args})")

                # Wait for tool execution
                tool_duration = 0.8
                start_time = time.time()
                with console.status(
                    "executing tool... (ctrl+c to interrupt)", spinner="dots"
                ) as status:
                    while time.time() - start_time < tool_duration:
                        elapsed = time.time() - start_time
                        status.update(
                            f"executing tool... ({elapsed:.1f}s ctrl+c to interrupt)"
                        )
                        await asyncio.sleep(0.1)

                tool_output = get_tool_output(tool_call)
                console.print(f"\t{tool_output.content}")
                await asyncio.sleep(0.3)

    except asyncio.CancelledError:
        raise


if __name__ == "__main__":
    chat()
