<h1 align="center">TinkerTasker</h1>
<p align="center">TinkerTasker is an open-source, local-first agent that runs in your terminal.
</p>


# Project Structure
```
`-- cli-ux
    `-- src
        `-- cli_ux
```


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
