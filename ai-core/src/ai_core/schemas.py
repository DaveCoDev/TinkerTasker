import json
import uuid

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolMessageParam
from pydantic import BaseModel, Field, SkipValidation
from pydantic_extra_types.pendulum_dt import DateTime


class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: DateTime = DateTime.now()
    chat_completion_message_param: SkipValidation[ChatCompletionMessageParam]


class MessageHistory(BaseModel):
    messages: list[Message] = []

    def get_messages(self) -> list[dict]:
        messages = [dict(msg.chat_completion_message_param) for msg in self.messages]
        return messages


class ToolCallData(BaseModel):
    name: str
    id: str
    args: dict


class AssistantMessageData(BaseModel):
    message: str | None = None
    tool_calls: list[ToolCallData] = []


class ToolMessageData(BaseModel):
    name: str
    id: str
    content: str


MessageData = AssistantMessageData | ToolMessageData


def create_message_data(
    assistant_response: dict | None = None,
    tool_call: dict | None = None,
    tool_message: ChatCompletionToolMessageParam | None = None,
) -> MessageData:
    """
    Create MessageData from OpenAI message components.

    For AssistantMessageData: pass assistant_response
    For ToolMessageData: pass tool_call and tool_message
    """
    if assistant_response is not None:
        tool_calls = assistant_response.get("tool_calls") or []
        return AssistantMessageData(
            message=assistant_response.get("content"),
            tool_calls=[
                ToolCallData(
                    name=call["function"]["name"],
                    id=call["id"],
                    args=json.loads(call["function"]["arguments"]),
                )
                for call in tool_calls
            ],
        )

    elif tool_call is not None and tool_message is not None:
        return ToolMessageData(
            name=tool_call["function"]["name"],
            id=tool_call["id"],
            content=tool_message["content"]
            if isinstance(tool_message["content"], str)
            else "",
        )

    else:
        raise ValueError(
            "Must provide either assistant_response or both tool_call and tool_message"
        )
