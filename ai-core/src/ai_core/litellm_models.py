import re
from typing import Any
import warnings

from openai.types.chat import ChatCompletionToolParam

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
    from litellm import acompletion


async def litellm_ollama_completion(
    model: str,
    messages: list[dict],
    tools: list[ChatCompletionToolParam] | None = None,
    api_base: str = "http://localhost:11434",
    num_ctx: int = 20000,
    num_predict: int = 4000,
    temperature: float = 0.7,
) -> Any:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="httpx")
        response = await acompletion(
            model=model,
            messages=messages,
            api_base=api_base,
            num_ctx=num_ctx,
            num_predict=num_predict,
            tools=tools,
            temperature=temperature,
        )
    return response


def strip_thinking(content: str | None) -> str | None:
    """Strip out <think>thinking content</think> tags and their content from model output."""
    if not content or not isinstance(content, str):
        return content
    pattern = r"<think>.*?</think>"
    return re.sub(pattern, "", content, flags=re.DOTALL).strip()
