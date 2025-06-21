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
