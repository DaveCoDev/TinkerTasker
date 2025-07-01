"""Setup script for TinkerTasker dependencies."""

import subprocess
import sys

from loguru import logger


def run_crawl4ai_setup() -> None:
    """Run the crawl4ai-setup command to configure crawl4ai after installation."""
    try:
        logger.info("Running crawl4ai-setup...")
        result = subprocess.run(
            ["crawl4ai-setup"],
            check=True,
            capture_output=True,
            text=True,
            shell=sys.platform == "win32",
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
