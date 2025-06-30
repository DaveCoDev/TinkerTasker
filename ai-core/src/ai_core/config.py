from pydantic import BaseModel


class LLMConfig(BaseModel):
    model_name: str = "ollama_chat/qwen3:30b-a3b-q4_K_M"
    max_completion_tokens: int = 4000
    temperature: float = 0.7
    num_ctx: int | None = 32000


class AgentConfig(BaseModel):
    max_steps: int = 25

    llm_config: LLMConfig = LLMConfig()
