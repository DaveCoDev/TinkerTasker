from collections.abc import AsyncGenerator
import json

from fastmcp import Client
from openai.types.chat import (
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
)

from ai_core.config import AgentConfig
from ai_core.litelllm_completion import (
    get_additional_llm_kwargs,
    litellm_completion,
    strip_thinking,
)
from ai_core.mcp_utils import mcp_tool_to_openai, parse_tool_call_content
from ai_core.prompts import AGENT_SYSTEM_PROMPT
from ai_core.schemas import Message, MessageData, MessageHistory, create_message_data


class Agent:
    def __init__(self, mcp_client: Client, config: AgentConfig) -> None:
        self.mcp_client = mcp_client
        self.config = config
        self.message_history = MessageHistory()
        self.message_history.messages.append(
            Message(
                chat_completion_message_param={
                    "role": "system",
                    "content": AGENT_SYSTEM_PROMPT,
                }
            )
        )

    async def handle_tool_call(
        self, tool_call: ChatCompletionMessageToolCallParam
    ) -> ChatCompletionToolMessageParam:
        """Parses the tool call and executes it using the MCP client."""
        tool_args = tool_call["function"]["arguments"]
        tool_args = json.loads(tool_args)

        result = await self.mcp_client.call_tool(
            name=tool_call["function"]["name"],
            arguments=tool_args,
            timeout=5,
        )
        content = parse_tool_call_content(result)

        tool_message = ChatCompletionToolMessageParam(
            role="tool",
            content=content,
            tool_call_id=tool_call["id"],
        )
        return tool_message

    async def turn(self, user_utterance: str) -> AsyncGenerator[MessageData, None]:
        """
        Executes an agentic loop that continues sending completion requests until
        there are no tool calls or MAX_STEPS is reached.

        Args:
            message (Message): The initial user message to start the conversation.
        """
        mcp_tools = await self.mcp_client.list_tools()
        mcp_tools = [mcp_tool_to_openai(tool) for tool in mcp_tools]
        self.message_history.messages.append(
            Message(
                chat_completion_message_param={
                    "role": "user",
                    "content": user_utterance,
                }
            )
        )

        for _ in range(self.config.max_steps):
            # Get the assistant response
            response = await litellm_completion(
                model=self.config.llm_config.model_name,
                messages=self.message_history.get_messages(),
                tools=mcp_tools,
                **get_additional_llm_kwargs(self.config.llm_config),
            )
            assistant_response = response.choices[0].message
            assistant_response["content"] = strip_thinking(
                assistant_response.get("content")
            )
            self.message_history.messages.append(
                Message(chat_completion_message_param=assistant_response)
            )
            tool_calls = assistant_response.get("tool_calls") or []
            yield create_message_data(assistant_response=assistant_response)

            # Handle tool calls
            if not tool_calls:
                break
            for tool_call in tool_calls:
                tool_message = await self.handle_tool_call(tool_call)
                self.message_history.messages.append(
                    Message(chat_completion_message_param=tool_message)
                )
                yield create_message_data(
                    tool_call=tool_call, tool_message=tool_message
                )
