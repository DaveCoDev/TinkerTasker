from pydantic import BaseModel


class LLMConfig(BaseModel):
    model_name: str = "ollama_chat/qwen3:30b-a3b-q4_K_M"
    max_completion_tokens: int = 4000
    temperature: float = 0.7
    num_ctx: int | None = 32000


class PromptConfig(BaseModel):
    knowledge_cutoff: str = "2024-10"
    timezone: str = "America/New_York"


class AgentConfig(BaseModel):
    max_steps: int = 25

    llm_config: LLMConfig = LLMConfig()

    prompt_config: PromptConfig = PromptConfig()
