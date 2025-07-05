<h1 align="center">TinkerTasker</h1>
<p align="center">TinkerTasker is an open-source, local-first agent that runs in your terminal.
</p>

<div align="center">
  <img src="assets/demo.gif" alt="TinkerTasker Demo" />
</div>

# Quickstart
1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

2. Install [Ollama](https://github.com/ollama/ollama?tab=readme-ov-file#ollama)

3. Pull the default model from Ollama:
   ```bash
   ollama run qwen3:30b-a3b-q4_K_M
   ```
   You can configure other models in the `config.yaml` that is generated (TinkerTasker will tell you the path).
4. Install as a uv tool
   ```bash
   uv tool install git+https://github.com/DaveCoDev/TinkerTasker#subdirectory=cli-ux
   uv run tinkertasker-setup
   ```

5. Run the CLI. It will use the current directory as the working directory which enables file editing. **Use at your own risk!**

   ```bash
   tinkertasker
   ```

## Updating

```bash
uv tool install <github url> --force
```

* **WARNING:** Currently your configuration will likely be reset when updating.
* Running `uv run tinkertasker-setup` again should not be currently necessary.


# Configuration Guide

TinkerTasker uses a YAML configuration file that's automatically created on first run. The configuration is stored at:

- **Windows:** `%APPDATA%\tinkertasker\config.yaml`
- **Linux** `~/.config/tinkertasker/config.yaml`


### LLM Configuration

```yaml
llm_config:
  model_name: "ollama_chat/qwen3:30b-a3b-q4_K_M"  # LiteLLM model to use
  max_completion_tokens: 4000 # Max tokens per response
  ... # Any other LiteLLM parameters can be added here
```

### Agent Configuration

```yaml
agent_config:
  max_steps: 25 # Maximum steps per agent turn
  
  prompt_config:
    knowledge_cutoff: "2024-10" # Knowledge cutoff date - set this depending on the model used
    timezone: "America/New_York" # Timezone for time in prompts
  
  native_mcp_servers:
    - filesystem # File system operations
    - web # Web browsing and search

  mcp_servers: [] # External MCP servers (see below)
```

### UX Configuration

```yaml
ux_config:
  number_tool_lines: 1 # Lines to show for tool outputs (-1 for all)
  max_arg_value_length: 100 # Max length for argument values in display
```

## Adding External MCP Servers

You can add external MCP servers to extend TinkerTasker's capabilities. For example:

```yaml
agent_config:
  mcp_servers:
    - identifier: "context7"
      command: "npx"
      args: ["-y", "@upstash/context7-mcp"]
      prefix: null # Optional prefix for tools
```

### Configuration Reset

If your configuration becomes corrupted or you want to start fresh, simply delete the config file. TinkerTasker will recreate it with default values on the next run.


# Project Structure
```
.
|-- ai-core
|   |-- src
|   |   `-- ai_core
|   |       `-- mcp_servers
|   |           |-- filesystem
|   |           `-- web
|   `-- tests
|       `-- mcp_servers
|           |-- filesystem
|           `-- web
`-- cli-ux
    `-- src
        `-- cli_ux
```


# Development

## Prerequisites

- [uv](https://docs.astral.sh/uv/#installation) for Python package management
- make
  - On Windows, you can install [winget](https://github.com/microsoft/winget-cli) then run `winget install ezwinports.make -e`
- [ollama](https://github.com/ollama/ollama?tab=readme-ov-file#ollama)


## Setup

- `make` - Run all commands below in sequence
- `make install` - Install and update dependencies for all Python packages
- `make lint` - Run ruff linting with auto-fix for all packages
- `make format` - Format code with ruff for all packages


# Development Environment Tutorial

## 1. Sample Environment Setup on Windows Subsystem for Linux (WSL 2)

1. Install WSL following [Developing in WSL](https://code.visualstudio.com/docs/remote/wsl)
1. Open a terminal and type `wsl.exe` to start WSL
1. `cd /home/<your-username>` to navigate to your home directory
1. Clone the repo `git clone https://github.com/DavidKoleczek/TinkerTasker.git`
1. `cd TinkerTasker` to enter the project directory
1. `code .` to open the project in Visual Studio Code
  1. If this doesn't work, you may need to add VSCode to path. 
  1. The repo should open and automatically install the WSL extensions. If it does not, click in the bottom left corner of VSCode and select WSL


## 2. Install [uv](https://docs.astral.sh/uv/#installation) to Manage Python Environments

1. Go to [Installation](https://docs.astral.sh/uv/#installation) and follow the instructions
1. Check if it installed correctly by running `uv --version` in your terminal


## 3. Setup AI Coding Tools

1. Setup [GitHub Copilot](https://code.visualstudio.com/docs/copilot/overview) for auto-completions and for quick questions.
1. Setup [Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup) and also let it install the VSCode extension.


## 4. Open VSCode Workspace

The project includes a VSCode workspace file (`TinkerTasker.code-workspace`) that configures the multi-package setup. Open it for the best development experience:

1. In VSCode, go to File → Open Workspace from File
2. Select `TinkerTasker.code-workspace`


## 5. Setup Development Environment

1. Install dependencies and set up all packages:
   ```bash
   make install
   ```

2. Before committing code, run linting and formatting:
   ```bash
   make lint
   make format
   ```

3. Or run everything at once:
   ```bash
   make
   ```

The project uses a Makefile to manage multiple Python packages (`ai-core` and `cli-ux`). Each command automatically handles virtual environments and runs the specified operations across all packages.


# Roadmap

To be determined based on interest.


# Attributions

This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
