import re
from typing import Any
import warnings

from openai.types.chat import ChatCompletionToolParam

from ai_core.config import LLMConfig

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
    from litellm import acompletion


async def litellm_completion(
    model: str,
    messages: list[dict],
    tools: list[ChatCompletionToolParam] | None = None,
    **kwargs: Any,
) -> Any:
    if model.startswith("ollama") and "api_base" not in kwargs:
        kwargs["api_base"] = "http://localhost:11434"

    if not model.startswith("ollama"):
        kwargs.pop("num_ctx", None)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="httpx")
        response = await acompletion(
            model=model,
            messages=messages,
            tools=tools,
            **kwargs,
        )
    return response


def strip_thinking(content: str | None) -> str | None:
    """Strip out <think>thinking content</think> tags and their content from model output."""
    if not content or not isinstance(content, str):
        return content
    pattern = r"<think>.*?</think>"
    return re.sub(pattern, "", content, flags=re.DOTALL).strip()


def get_additional_llm_kwargs(llm_config: LLMConfig) -> dict[str, Any]:
    """Get the additional kwargs from the config."""
    addition_kwargs = {
        "max_completion_tokens": llm_config.max_completion_tokens,
        "temperature": llm_config.temperature,
    }

    if llm_config.num_ctx is not None:
        addition_kwargs["num_ctx"] = llm_config.num_ctx

    return addition_kwargs
