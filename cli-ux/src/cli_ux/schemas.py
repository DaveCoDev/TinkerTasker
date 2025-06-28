from collections.abc import Callable
import time
from typing import Any

from pydantic import BaseModel


class UserMessage(BaseModel):
    content: str


class ToolCall(BaseModel):
    name: str
    id: str
    args: str


class AssistantResponseMessage(BaseModel):
    message: str | None
    tool_calls: list[ToolCall] = []


class ToolMessage(BaseModel):
    name: str
    id: str
    content: str


MessageEvent = UserMessage | AssistantResponseMessage | ToolMessage


class EventBus:
    """Simple event bus for publishing and subscribing to message events."""

    def __init__(self):
        self._subscribers: list[Callable[[MessageEvent], None]] = []

    def subscribe(self, handler: Callable[[MessageEvent], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, event: MessageEvent) -> None:
        for handler in self._subscribers:
            handler(event)


class TurnContext:
    """Context manager for a complete user turn with timing and event queue."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.start_time: float = 0
        self.is_processing = False

    async def __aenter__(self):
        self.start_time = time.time()
        self.is_processing = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.is_processing = False

    def emit_event(self, event: MessageEvent) -> None:
        self.event_bus.publish(event)

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time
