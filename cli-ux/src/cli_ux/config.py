import os
from pathlib import Path
import platform

from ai_core.config import AgentConfig
from pydantic import BaseModel, Field
import yaml


class UXConfig(BaseModel):
    number_tool_lines: int = Field(
        default=1,
        description="number of lines to display for tool outputs. -1 for all",
    )


class CLIConfig(BaseModel):
    version: str = "0.1.0"
    agent_config: AgentConfig = AgentConfig()
    ux_config: UXConfig = UXConfig()


def get_config_path() -> Path:
    """Get the full path to the config file."""
    system = platform.system()
    if system == "Windows":
        config_dir = Path(
            os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        )
    else:
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_dir / "tinkertasker" / "config.yaml"


def load_config() -> CLIConfig:
    """Load configuration from YAML file or create default if it doesn't exist.
    Resets to the default config if the file is invalid or the version has changed.
    """
    config_path = get_config_path()

    def create_default_config() -> CLIConfig:
        """Create and save a default configuration."""
        config = CLIConfig()
        save_config(config)
        return config

    if not config_path.exists():
        return create_default_config()

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            return create_default_config()

        config = CLIConfig(**config_data)

        # Check if version has changed
        current_version = CLIConfig().version
        if config.version != current_version:
            return create_default_config()
        return config
    except Exception:
        return create_default_config()


def save_config(config: CLIConfig) -> None:
    """Save configuration to YAML file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_dict = config.model_dump()
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
