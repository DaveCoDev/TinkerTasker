<h1 align="center">TinkerTasker</h1>
<p align="center">TinkerTasker is an open-source, local-first agent that runs in your terminal.
</p>

# Quickstart
<todo later this will be how to install it on Windows and Linux>

# Configuration Guide
<todo later this will be how to customize the project>


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
