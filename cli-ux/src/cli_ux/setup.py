"""Setup script for TinkerTasker dependencies."""

import os
from pathlib import Path
import subprocess
import sys

from loguru import logger


def run_crawl4ai_setup() -> None:
    try:
        logger.info("Running crawl4ai-setup...")

        # Set up environment for Windows to handle encoding issues
        env = os.environ.copy()
        if sys.platform == "win32":
            env["PYTHONIOENCODING"] = "ascii:replace"

        # Add the Scripts directory to PATH so crawl4ai-setup can be found
        python_dir = Path(sys.executable).parent

        # Check if we're already in the Scripts/bin directory
        if sys.platform == "win32":
            scripts_dir = (
                python_dir if python_dir.name == "Scripts" else python_dir / "Scripts"
            )
        else:
            scripts_dir = python_dir if python_dir.name == "bin" else python_dir / "bin"

        # Prepend the scripts directory to PATH
        current_path = env.get("PATH", "")
        env["PATH"] = f"{scripts_dir}{os.pathsep}{current_path}"

        logger.info(f"Added to PATH: {scripts_dir}")

        result = subprocess.run(
            ["crawl4ai-setup"],
            check=True,
            capture_output=True,
            text=True,
            shell=sys.platform == "win32",
            env=env,
        )
        logger.success("crawl4ai-setup completed successfully")
        if result.stdout:
            print(result.stdout)

    except subprocess.CalledProcessError as err:
        logger.error(f"crawl4ai-setup failed with exit code {err.returncode}")
        if err.stdout:
            print("STDOUT:", err.stdout)
        if err.stderr:
            print("STDERR:", err.stderr)
        sys.exit(1)

    except FileNotFoundError:
        logger.error(
            "crawl4ai-setup command not found. Make sure crawl4ai is installed."
        )
        sys.exit(1)


def main() -> None:
    run_crawl4ai_setup()


if __name__ == "__main__":
    main()
